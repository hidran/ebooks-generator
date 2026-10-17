# Capítulo 9. Skills, de comando a capacidad reutilizable

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

- Cuándo conviene convertir un comando personalizado en skill y qué te aporta la carpeta adicional.
- Cómo está hecho un `SKILL.md`: los campos del frontmatter y una description que active la skill en el momento justo.
- Dos skills escritas a mano: `report-pdf`, que saca un informe PDF de un CSV, y `data-analysis-saas-monthly`, con scripts, referencias y plantillas.
- Cómo usar el skill-creator, dónde encontrar skills ya hechas y cómo mantener en orden las que vas acumulando.

[Requisitos previos]{.callout-title}

El capítulo 8 (archivos de comando, argumentos, `` !`comando` ``), el proyecto `analisi-saas` de los capítulos 4-6 y el laboratorio `cc-advanced-lab` del capítulo 2.

:::

En el capítulo 8 escribiste comandos en `.claude/commands/`: un archivo, un prompt, una barra para llamarlo. Funcionan de maravilla mientras el prompt se baste solo. Cuando el comando necesita una guía de estilo, una plantilla para el correo o un script de Python que haga las cuentas siempre de la misma manera, el archivo único se queda corto. O lo pegas todo dentro, y cada invocación arrastra páginas que sirven una vez de cada diez, o escribes "busca el script en algún sitio" y cruzas los dedos.

Una skill es lo mismo con una carpeta alrededor. Las instrucciones van en `SKILL.md`, al lado pones los archivos de apoyo, y Claude los lee o los ejecuta solo cuando hacen falta. La description funciona como interruptor: cuando tu petición encaja con ella, Claude carga la skill por su cuenta. Un compañero recién llegado que escribe "¿me preparas el informe de junio?" obtiene el procedimiento del equipo sin saber que existe.

## 9.1 Comandos y skills, un solo sistema

En la primera edición, comandos y skills eran dos mecanismos separados, y los comandos parecían destinados a desaparecer. Hoy Claude Code los ha fusionado. Un archivo `.claude/commands/report.md` y una skill `.claude/skills/report/SKILL.md` crean los dos `/report` y funcionan igual. Los archivos de comando son el formato más antiguo, siguen funcionando y aceptan el mismo frontmatter que las skills, salvo `name` y `paths`. Para trabajo nuevo la documentación recomienda las skills, y si un comando y una skill tienen el mismo nombre, gana la skill.

Así que la elección tiene que ver con la forma: un solo archivo o una carpeta. Yo lo decido así:

| Necesitas | Formato |
| :---- | :---- |
| Un prompt reutilizable, sin archivos de apoyo | Archivo en `.claude/commands/`, o skill con solo `SKILL.md` |
| Un procedimiento que ejecuta scripts de Python o Bash | Skill con `scripts/` |
| Guías, reglas de cálculo o ejemplos que consultar solo cuando hacen falta | Skill con `references/` |
| Textos base para la salida, como un correo o un encabezado | Skill con `templates/` |
| Activación automática solo con ciertos archivos del proyecto | Skill con `paths` |

Dos ejemplos del libro. `/fix-tests` del capítulo 8 sigue siendo un comando: es un prompt y no necesita nada alrededor. El informe mensual SaaS del capítulo 6, en cambio, tiene tres scripts, unas reglas de cálculo y un texto fijo para el correo, así que se convierte en la skill `data-analysis-saas-monthly` de la sección 9.4. Pasa a la carpeta cuando te des cuenta de que estás pegando recursos en el archivo del comando solo para tenerlos cerca del prompt.

## 9.2 Anatomía de una skill

### La carpeta

Una skill es una carpeta con un nombre en minúsculas y con guiones, que contiene como mínimo un archivo `SKILL.md`. Todo lo demás es opcional. Esta es la estructura que uso:

```text
.claude/skills/nombre-skill/
├── SKILL.md          obligatorio: frontmatter e instrucciones
├── references/       guías y reglas, se leen cuando hacen falta
│   ├── style-guide.md
│   └── business-rules.md
├── scripts/          scripts que se ejecutan
│   ├── analyze.py
│   └── generate-report.sh
└── templates/        bases para la salida
    ├── email-summary.txt
    └── report-header.md
```

Los nombres de las subcarpetas son una convención: Claude Code no los trata de forma especial, y el skill-creator de Anthropic llama `assets/` a la de las plantillas. Lo que cuenta es que `SKILL.md` diga cuándo abrir cada archivo. Claude Code carga una skill en tres niveles:

1. El nombre y la description están en el contexto de cada sesión, aunque no uses la skill. De ahí saca Claude cuándo le serviría.
2. El cuerpo de `SKILL.md` entra en el contexto cuando la skill se activa o cuando la invocas tú.
3. Los archivos de apoyo entran solo cuando Claude los lee, siguiendo las instrucciones del cuerpo. Los scripts se ejecutan, y al contexto llega solo su salida.

El primer nivel tiene un coste que pagas siempre, y `/skills` te lo muestra skill por skill.

![La lista de /skills con las skills de proyecto y las personales, cada una con el peso de su description en tokens](figures/cap-09/fig-02.png)

Cada sección lee a la vez `.claude/skills` y `.claude/commands`. Conviene que el segundo nivel sea corto: el skill-creator sugiere no pasar de 500 líneas y mover el resto a archivos separados, referenciados desde `SKILL.md`.

### El frontmatter

`SKILL.md` empieza con un bloque YAML entre dos líneas `---`, seguido de las instrucciones en Markdown. Todos los campos son opcionales, pero sin `description` Claude no tiene forma de saber cuándo usar la skill. Los que de verdad vas a necesitar:

| Campo | Para qué sirve |
| :---- | :---- |
| `name` | El nombre, y por tanto el comando: `report-pdf` se convierte en `/report-pdf`. Minúsculas, números y guiones. Si falta, se usa el nombre de la carpeta |
| `description` | Qué hace la skill y cuándo usarla. Claude decide a partir de aquí si cargarla |
| `when_to_use` | Otros casos en los que usarla, añadidos a la description. Juntas se truncan a 1536 caracteres |
| `argument-hint` | La pista sobre los argumentos que aparece en el menú, por ejemplo `<file-csv>` |
| `arguments` | Los nombres de los argumentos posicionales, que se usan en el cuerpo como `$nombre` |
| `disable-model-invocation` | Con `true`, la skill se ejecuta solo cuando la escribes tú |
| `user-invocable` | Con `false`, desaparece del menú `/` y solo la usa Claude |
| `allowed-tools` | Los tools que Claude usa sin preguntar mientras la skill está activa |
| `model`, `effort` | Modelo y nivel de razonamiento para el resto del turno |
| `context: fork` | Ejecuta la skill en un subagente; el campo `agent` indica cuál |
| `paths` | Globs que limitan la activación automática a los archivos que coinciden |

Los argumentos funcionan como en los comandos del capítulo 8: `$ARGUMENTS` lo toma todo, `$0`, `$1` y así sucesivamente toman las palabras por posición, y `${CLAUDE_SKILL_DIR}` es la ruta de la carpeta de la skill, útil para lanzar sus scripts desde cualquier directorio. Con `arguments` les pones nombre a las posiciones y el cuerpo se lee mejor: `$csv` en lugar de `$0`. Lo usas en la sección 9.4.

Con `allowed-tools` hay un malentendido frecuente. El campo solo añade permisos: los tools de la lista se ejecutan sin confirmación mientras la skill está activa, hasta tu siguiente mensaje, y los demás siguen disponibles con los permisos normales de la sesión. Para impedir que una skill use un tool, el campo es `disallowed-tools`.

Con `context: fork` la skill se ejecuta en un subagente con su propio contexto, que empieza vacío. No ve la conversación, así que el cuerpo de `SKILL.md` tiene que contener todo lo necesario. Desde la versión 2.1.218 una skill en fork se ejecuta en segundo plano y tu turno no la espera; para esperar el resultado, añade `background: false`. Sirve para los trabajos largos que llenarían el contexto principal de salida intermedia (los subagentes son el tema del capítulo 10).

Si también quieres subir la skill a claude.ai o usarla con la API, el estándar Agent Skills acepta solo `name`, `description`, `license`, `compatibility`, `metadata` y `allowed-tools`; el resto es una extensión de Claude Code.

### La description es el disparador

El error más común la primera vez es escribir la description como documentación para un compañero. La lee un modelo, que con esas dos líneas tiene que averiguar si tu petición entra en la skill. Una description vaga da como resultado una skill que no se activa nunca, o que se activa cuando no viene a cuento:

```yaml
# demasiado vaga
description: Analiza datos.
```

Esta, en cambio, dice qué hace, sobre qué datos y con qué palabras la pedirá el usuario:

```yaml
# precisa
description: Hace un análisis estadístico de una columna de un archivo CSV
  (tipo, count, valores faltantes, media, desviación estándar, mín., máx.,
  cuartiles, outliers). Úsala cuando el usuario pida analizar,
  describir, perfilar o inspeccionar una columna, también en inglés
  (describe column, profile column).
```

Empieza por lo que hace, con un verbo. Nombra el dominio (CSV, columna, informe) y los formatos. Añade una frase explícita sobre cuándo usarla, con las palabras que de verdad usará quien escriba el prompt: si el equipo trabaja en español y en inglés, ponlas en los dos idiomas. Las instrucciones del skill-creator añaden un consejo útil. Claude tiende a usar las skills menos de lo que debería, así que una description algo insistente ("úsala aunque el usuario no mencione explícitamente el informe") funciona mejor que una prudente. El límite contrario es la longitud: la description pesa en cada sesión, y cuatro o cinco líneas bastan casi siempre.

Un último detalle explica muchos "mi skill no se ejecuta": Claude consulta las skills para las tareas que no resuelve fácilmente por sí solo. Una petición de un solo paso, como "lee este archivo", puede no activar ninguna skill aunque la description sea perfecta, porque Claude la resuelve directamente con los tools básicos. Las peticiones de varios pasos, o propias de un dominio, son las que marcan la diferencia en la description.

## 9.3 La primera skill: report-pdf

Empieza por una skill pequeña, en el laboratorio del capítulo 2. `cc-advanced-lab` tiene un CSV de tres filas, `data/vendite.csv`, con las ventas de enero, febrero y marzo de 2026. La skill `report-pdf` saca de él una tabla de resumen en el chat y el mismo informe en PDF, con ReportLab como en el capítulo 6.

```bash
cd ~/cc-advanced-lab
mkdir -p .claude/skills/report-pdf
```

Crea `.claude/skills/report-pdf/SKILL.md`:

```markdown
---
name: report-pdf
description: Prepara un informe de ventas a partir de un archivo CSV, con una tabla de resumen en el chat y el mismo informe en PDF en la carpeta output/. Úsala cuando el usuario pida un informe, un resumen, los totales o un PDF a partir de un archivo CSV.
argument-hint: <file-csv>
allowed-tools: Read Write Bash(python3 *)
---

El archivo que hay que usar es $ARGUMENTS. Si está vacío, usa el CSV
mencionado en la petición; si no hay ninguno, pregunta cuál analizar.

1. Lee el CSV e identifica la columna numérica.
2. Responde con una tabla Markdown con el número de filas, el total,
   el mínimo, el máximo y la media de la columna, la media con dos
   decimales.
3. Crea output/report-<nombre del CSV sin extensión>.pdf con ReportLab:
   título "Informe de ventas", la fecha de hoy, la tabla del paso 2 y,
   debajo, todas las filas del CSV. Usa el script output/genera_pdf.py,
   que recibe la ruta del CSV como primer argumento: si no existe,
   escríbelo y luego ejecútalo con python3.
4. Si ReportLab no está instalado, detente y sugiere
   `pip install reportlab`. No lo instales tú.

No modifiques nunca el CSV de entrada.
```

La description contiene las palabras con las que pedirás el trabajo: informe, resumen, totales, PDF, CSV. `allowed-tools` evita las confirmaciones para el script y para `python3` en modo Manual. El paso 3 hace que se reutilice el script si ya existe: la primera vez Claude lo escribe, y a partir de la segunda el PDF sale siempre igual. La skill cabe entera en un archivo a propósito, porque en el capítulo 14 la copias a un plugin con un solo `cp` de `SKILL.md`. ReportLab, en cambio, sí lo necesitas: si falta en el entorno de Python del laboratorio, `pip install reportlab`.

Si Claude Code ya estaba abierto, lanza `/reload-skills`, que vuelve a leer las carpetas de skills y de comandos, y luego `/skills`: `report-pdf` tiene que aparecer entre las skills de proyecto. Ahora pruébala sin nombrarla:

```text
¿me preparas un informe en PDF de las ventas de data/vendite.csv?
```

Claude carga la skill y responde con la tabla. Los números tienen que ser estos: 3 filas, total 358, mínimo 95, máximo 143, media 119,33. El total es el mismo que comprueba `tests/test_report.py`, así que tienes una verificación inmediata. El PDF acaba en `output/report-vendite.pdf`. Luego prueba la invocación explícita, que es la que usarás en los scripts y en el capítulo 14:

```text
/report-pdf data/vendite.csv
```

Si con el prompt en lenguaje natural Claude responde sin cargar la skill, el problema casi siempre es la description: no contiene las palabras con las que lo has pedido. Cuando funcione, haz commit de `.claude/skills/report-pdf/`, y si no quieres los PDF en el repositorio, añade `output/` al `.gitignore`.

## 9.4 Una skill completa: data-analysis-saas-monthly

Ahora la skill que se anticipó en el capítulo 6. A partir de un CSV de métricas SaaS como `saas_metrics.csv` produce tres archivos para un cliente (el informe PDF, un dashboard HTML estático con Chart.js que se abre sin servidor y el Excel con los datos y el resumen) y el correo que los acompaña.

La pongo en el proyecto porque las columnas y las reglas de cálculo son de este proyecto: en `~/.claude/skills/` pesaría en el contexto de todas las sesiones, incluso donde no sirve.

### Paso 1: la estructura

```bash
cd ~/progetti/analisi-saas
mkdir -p .claude/skills/data-analysis-saas-monthly/{scripts,references,templates}
```

Si lo prefieres, pídeselo a Claude con un prompt de una línea: para las carpetas da igual.

### Paso 2: SKILL.md

Crea `.claude/skills/data-analysis-saas-monthly/SKILL.md`:

```markdown
---
name: data-analysis-saas-monthly
description: Genera el informe mensual SaaS de un cliente a partir de un CSV de métricas (mrr, churn_rate, plan, region) y produce un PDF, un dashboard HTML y un Excel. Úsala cuando el usuario pida el informe mensual, el análisis del mes o un resumen de MRR y churn para un cliente, aunque no mencione los formatos (monthly report, SaaS metrics, MRR report).
argument-hint: <csv> <cliente> <mese>
arguments: [csv, cliente, mese]
allowed-tools: Read Bash(python3 *)
---

# Informe mensual SaaS

Entrada: el CSV $csv, el cliente $cliente, el mes $mese.
Si falta alguno de los tres, pídelo antes de empezar.
Todos los archivos generados van en output/$cliente/.
Las rutas references/, scripts/ y templates/ son relativas a
${CLAUDE_SKILL_DIR}.

## Recursos

- references/struttura-csv.md: columnas obligatorias y opcionales.
- references/regole-metriche.md: cómo se calculan las métricas derivadas.
- templates/email-riepilogo.txt: el correo que acompaña a los archivos.
- scripts/: los scripts se ejecutan, no hace falta leerlos.

## Fase 1: validación

1. Compara las columnas de $csv con references/struttura-csv.md.
   Si falta una columna obligatoria, detente y dime cuál.
2. Ejecuta `python3 ${CLAUDE_SKILL_DIR}/scripts/metriche.py $csv output/$cliente`.
   El script imprime el resumen por mes y escribe metriche.xlsx.

## Fase 2: análisis

3. Aplica al resumen references/regole-metriche.md: variación
   mes a mes, outliers, tendencia de los últimos tres meses.
4. No recalcules a mano los números que el script ya ha impreso.

## Fase 3: salida

5. Ejecuta scripts/genera_grafici.py y scripts/genera_report.py con
   `--csv $csv --outdir output/$cliente`; a genera_report.py pásale
   también `--cliente "$cliente, $mese"`.
6. Escribe output/$cliente/dashboard.html: una sola página con Chart.js
   desde un CDN y los datos del resumen incrustados como JSON, sin servidor.
7. Rellena templates/email-riepilogo.txt y guárdalo como
   output/$cliente/email.txt.

## Fase 4: cierre

8. Enumera los archivos generados con su ruta.
9. Indica las tres métricas que merecen atención y por qué.
10. Propón un siguiente paso concreto.
```

Las fases también te sirven a ti: cuando algo sale mal, ves enseguida si el trabajo se quedó en la validación o en la salida. El paso 4 está ahí porque, sin él, Claude puede rehacer las cuentas por su cuenta sobre el CSV y llegar a un total distinto del que da el script. Así los números los calcula el código y Claude se encarga de comentarlos.

### Paso 3: las referencias

`references/struttura-csv.md` describe el CSV que la skill espera, con las columnas del dataset del capítulo 4:

```markdown
# Estructura esperada del CSV

Columnas obligatorias:
- month (int, 1-12)
- plan (string: free | silver | gold)
- region (string: Europe | North America | Asia Pacific)
- new_signups (int)
- cancellations (int)
- mrr (float, euros)
- churn_rate (float, porcentaje)

Columnas opcionales (si faltan, omite las métricas que las usan):
- date (YYYY-MM-DD)
- retention_rate
- support_tickets
- ai_voice_usage, ai_text_usage
```

`references/regole-metriche.md` fija las reglas de negocio, las que de otro modo Claude interpretaría a su manera cada vez:

```markdown
# Reglas para las métricas

- MRR del mes: suma de mrr en las filas silver y gold. El plan free
  no contribuye y se excluye.
- Variación MoM: (MRR del mes - MRR del mes anterior) / MRR del mes anterior.
- Churn del mes: media de churn_rate en las filas de pago. En el informe
  llámalo "churn medio", porque no se recalcula sobre los clientes.
- Outliers: valores a más de 2 desviaciones estándar de la media de la misma
  combinación de plan y región. Se señalan, no se eliminan.
- Tendencia: regresión lineal simple sobre el MRR de los últimos tres meses.
```

### Paso 4: los scripts

Dos de los scripts ya los tienes: `genera_grafici.py` y `tools/genera_report.py` del capítulo 6. Trabajan sobre el CSV del proyecto, así que en las copias para la skill hay que poder indicar el archivo y la carpeta de salida:

```text
Copia tools/genera_grafici.py y tools/genera_report.py en
.claude/skills/data-analysis-saas-monthly/scripts/.
En las copias añade los argumentos --csv (archivo de entrada) y --outdir
(carpeta de salida, por defecto output/); a genera_report.py añádele
también --cliente, que debe aparecer en el título del PDF.
No toques los originales de tools/.
```

El tercer script es nuevo. Valida las columnas, calcula el resumen por mes y escribe el Excel. Guárdalo como `.claude/skills/data-analysis-saas-monthly/scripts/metriche.py`:

```python
#!/usr/bin/env python3
"""Valida il CSV delle metriche SaaS, stampa il sommario e scrive l'Excel.

Uso: python3 metriche.py <csv> <cartella-output>
"""
import sys
from pathlib import Path

import pandas as pd

RICHIESTE = [
    "month", "plan", "region", "new_signups",
    "cancellations", "mrr", "churn_rate",
]


def carica(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    mancanti = [c for c in RICHIESTE if c not in df.columns]
    if mancanti:
        sys.exit(f"Colonne mancanti: {mancanti}")
    return df


def sommario(df: pd.DataFrame) -> pd.DataFrame:
    pagati = df[df["plan"] != "free"]
    per_mese = pagati.groupby("month").agg(
        mrr=("mrr", "sum"),
        nuovi=("new_signups", "sum"),
        cancellazioni=("cancellations", "sum"),
        churn_medio=("churn_rate", "mean"),
    )
    per_mese["mrr_mom_pct"] = per_mese["mrr"].pct_change() * 100
    return per_mese.round(2).reset_index()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("Uso: python3 metriche.py <csv> <cartella-output>")
    df = carica(sys.argv[1])
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    tabella = sommario(df)
    with pd.ExcelWriter(out / "metriche.xlsx", engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Dati", index=False)
        tabella.to_excel(writer, sheet_name="Sommario", index=False)
    print(tabella.to_string(index=False))
    print(f"Excel scritto in {out / 'metriche.xlsx'}")
```

El script imprime el resumen en stdout porque así es como los números llegan a Claude: al contexto entra la tabla de seis filas, no el código ni las 54 filas del CSV. Si falta una columna obligatoria, sale con un mensaje claro, y Claude te transmite eso en lugar de analizar datos equivocados.

### Paso 5: la plantilla del correo

`templates/email-riepilogo.txt`:

```text
Asunto: Informe SaaS mensual, [CLIENTE] [MES]

Hola, [NOMBRE]:

aquí tienes el resumen de las métricas de [CLIENTE] de [MES].

NÚMEROS DEL MES
MRR total:         [MRR_TOTAL] EUR
Variación MoM:     [DELTA_MOM]%
Churn medio:       [CHURN]%
Nuevos registros:  [NUEVOS]

TRES COSAS QUE MIRAR
1. [PUNTO_1]
2. [PUNTO_2]
3. [PUNTO_3]

ADJUNTOS
report.pdf       informe completo con gráficos
metriche.xlsx    datos en bruto y resumen por mes
dashboard.html   gráficos interactivos, se abre en el navegador

SIGUIENTE PASO
[SUGERENCIA]

Generado con Claude Code, skill data-analysis-saas-monthly
```

### Paso 6: la prueba

Lanza `/reload-skills` y comprueba con `/skills` que la skill aparece entre las de proyecto. Luego pide el trabajo sin nombrarla, como lo haría un compañero:

```text
Tengo las métricas SaaS de junio en data/saas_metrics.csv.
¿Me preparas el informe mensual para startup_alpha?
```

Claude carga la skill, ejecuta `metriche.py`, lee las reglas, genera los archivos en `output/startup_alpha/` y cierra con la lista de archivos y las tres métricas que vigilar. La forma explícita, útil cuando tienes varios clientes seguidos como la agencia del capítulo 6, es:

```text
/data-analysis-saas-monthly data/saas_metrics.csv startup_alpha junio
```

### Los casos límite

Después de las primeras pruebas siempre aparece alguno: un cliente con menos columnas, un CSV exportado en latin-1 desde un software de gestión antiguo, un mes con MRR a cero que rompe la variación mes a mes. Añade una sección al final de `SKILL.md`:

```markdown
## Casos límite

- Faltan columnas opcionales: omite las métricas que las usan y
  dilo en el resumen ejecutivo.
- MRR del mes anterior a cero (cliente nuevo): la variación MoM
  es n/d, no un error ni un valor infinito.
- No se encuentra el CSV: pide la ruta completa antes de continuar.
- El script falla con UnicodeDecodeError: guarda una copia del CSV
  en UTF-8 en output/$cliente/ y vuelve a ejecutarlo sobre esa copia.
```

Añade una regla cada vez y pruébala con un CSV construido a propósito. Si un cambio en `SKILL.md` no parece haber llegado, `/reload-skills`.

## 9.5 El skill-creator

Escribir `SKILL.md` a mano sirve para entender cómo está hecha una skill. En el trabajo diario es más rápido el skill-creator, una skill de Anthropic que construye otras skills a través de una conversación y luego las pone a prueba. Se instala como plugin desde el marketplace oficial:

```text
/plugin install skill-creator@claude-plugins-official
```

Después de `/reload-plugins` la invocas con el prefijo del plugin, `/skill-creator:skill-creator`, o escribes que quieres crear o mejorar una skill y dejas que se active sola. Si entras con una cuenta de claude.ai que tiene el skill-creator activado, la skill llega ya sincronizada: `/skills` la muestra en `claude.ai sync` y la lanzas como `/anthropic-skills:skill-creator`, sin instalar el plugin.

### Cómo trabaja

Lo primero que hace es mirar la conversación. Si acabas de hacer un trabajo a mano, por ejemplo los gráficos de un CSV, te propone convertirlo en una skill y saca los pasos del historial.

![El skill-creator propone opciones según la conversación: mejorar una skill que se acaba de usar, crear una nueva o convertir en skill el trabajo con los gráficos](figures/cap-09/fig-01.png)

Si empiezas de cero, te hace cuatro preguntas: qué debe hacer la skill, cuándo debe activarse, qué formato tiene la salida y si quieres casos de prueba. Luego pregunta por los casos límite, los formatos de entrada y las dependencias. Para una skill de profiling de CSV, a la pregunta sobre qué hacer y cuándo basta una respuesta como esta:

```text
Analiza un archivo CSV con un profiling completo para detectar anomalías
y outliers. Úsala cuando el usuario pida analizar, perfilar, describir o
revisar una columna o un dataset, o cuando pida encontrar outliers
o anomalías estadísticas.
```

De esta respuesta sale la description del frontmatter, ya escrita para activar la skill. Si en la conversación dices que puede usar Python, el skill-creator también escribe el script en `scripts/`.

La parte que justifica la instalación es la verificación. El skill-creator escribe algunos prompts de prueba y, para cada uno, lanza dos subagentes en el mismo turno, uno con la skill y otro sin ella. Ves los resultados uno al lado del otro en una página del navegador, comentas cada salida, y él reescribe la skill y vuelve a lanzarla. Si nota que todas las ejecuciones han escrito el mismo script de apoyo, te propone ponerlo en `scripts/` de una vez por todas.

Al final propone optimizar la description. Prepara una veintena de peticiones, la mitad que deben activar la skill y la otra mitad que se le parecen pero no deben activarla, lanza cada una tres veces, prueba hasta cinco versiones de la description y se queda con la que mejor funciona en un grupo de peticiones reservado aparte. Cada ejecución consume tu plan, así que en una skill trivial sáltate este paso.

### Cuándo prescindir de él

El skill-creator compensa cuando la skill tiene scripts o cuando quieres medir la diferencia con y sin skill antes de compartirla. Escribo a mano cuando modifico una skill existente y cuando la skill es un `SKILL.md` de veinte líneas como `report-pdf`: ahí las entrevistas y los benchmarks cuestan más que la propia skill. Los dos caminos se combinan, con el scaffolding del skill-creator y el acabado a mano. Si instalaste Superpowers en el capítulo 8, su skill `writing-skills` cubre el mismo terreno con un enfoque más cercano al TDD.

::: {.callout .callout-prompt}
[Prompt reutilizable]{.callout-title}

El esbozo de una skill nueva, para dárselo a Claude directamente o para aclararte las ideas antes de usar el skill-creator:

```text
Quiero crear una skill para Claude Code que se llame [NOMBRE-SKILL].

Debe activarse cuando el usuario pida [DESCRIBE EL DISPARADOR CON PALABRAS NATURALES].
El flujo de trabajo tiene estos pasos:
1. [PASO 1]
2. [PASO 2]
3. [PASO 3]

¿Necesita [scripts de Python / references / templates]? [SÍ/NO, especifica]

Crea la estructura de carpetas en .claude/skills/[NOMBRE-SKILL]/ (o en
~/.claude/skills/[NOMBRE-SKILL]/ si la necesito en todos mis proyectos),
escribe SKILL.md con un frontmatter optimizado para la activación automática
y añade los archivos de apoyo que hagan falta en las subcarpetas adecuadas.
```
:::

## 9.6 Skills ya hechas

Antes de escribir una skill desde cero, busca si alguien ya la ha hecho. Las skills de terceros llegan casi siempre dentro de un plugin, desde un marketplace. El oficial de Anthropic, `claude-plugins-official`, viene configurado desde el primer arranque; el de la comunidad, `claude-community` (repositorio `anthropics/claude-plugins-community`), lo añades cuando en el oficial no encuentras lo que buscas. En el oficial muchos vendors publican sus skills: en octubre de 2026 había, por ejemplo, `duckdb-skills` y `huggingface-skills`, junto al skill-creator y a Superpowers. Los exploras en la pestaña Discover de `/plugin`; el capítulo 14 explica cómo evaluarlos.

Para un desarrollador, el punto de partida sigue siendo Superpowers, que instalaste en el capítulo 8. Sus skills que conviene conocer desde ya:

| Skill | Qué hace |
| :---- | :---- |
| `test-driven-development` | Guía el ciclo TDD: primero el test que falla, luego el código |
| `systematic-debugging` | Divide la depuración en fases: reproducción, hipótesis, verificación, fix |
| `brainstorming` | Explora las alternativas de diseño antes de escribir código |
| `verification-before-completion` | Comprueba que el trabajo esté terminado de verdad antes de darlo por cerrado |
| `writing-skills` | Diseña y verifica skills nuevas |

Para la code review no hace falta un plugin: `/code-review` es una skill incluida en Claude Code, y la usas con la Photogallery en el capítulo 22.

::: {.callout .callout-warning}
[Atención]{.callout-title}

Antes de instalar una skill de terceros, abre su `SKILL.md` en el repositorio y léelo. Las líneas `` !`comando` `` se ejecutan en tu máquina en cuanto la skill se activa, antes de que Claude vea nada, y los scripts de `scripts/` se ejecutan con tus permisos. Al leerlo también descubres qué espera del proyecto: algunas skills dan por hecha una determinada estructura de carpetas o herramientas ya instaladas, como pytest o eslint. Si no te fías de la inyección de comandos, `"disableSkillShellExecution": true` en la configuración la desactiva.
:::

Una skill tuya la quitas borrando su carpeta. Las de los plugins se gestionan desde el plugin: la pestaña Installed de `/plugin` lo desactiva o lo elimina, y desde la terminal tienes `claude plugin update` y `claude plugin uninstall`.

## 9.7 Organizar las skills

### Dónde viven

| Nivel | Ruta | Notas |
| :---- | :---- | :---- |
| Personal | `~/.claude/skills/<nombre>/SKILL.md` | En todos tus proyectos, en esta máquina |
| Proyecto | `.claude/skills/<nombre>/SKILL.md` | En el repositorio, la recibe quien lo clona |
| Subcarpeta | `<carpeta>/.claude/skills/...` | Con nombres repetidos se invoca como `/apps/web:deploy` |
| `--add-dir` | `.claude/skills/` en las carpetas añadidas | Útil para pruebas |
| Plugin | `<plugin>/skills/<nombre>/SKILL.md` | Con el prefijo: `/nombre-plugin:nombre-skill` |
| Cuenta de claude.ai | Skills sincronizadas | Prefijo `anthropic-skills:` |

La regla que sigo: en `~/.claude/skills/` van los flujos genéricos que uso en todas partes, en `.claude/skills/` los ligados al dominio del proyecto, como las dos skills de este capítulo. Las skills de proyecto se suben con un commit, y quien hace `git pull` las recibe sin instrucciones de setup.

### Nombres y sincronización

Al cabo de unos meses, una lista de carpetas como `report-generator`, `my-skill-v2`, `test-cosa` ya no te dice qué es estable y qué es un experimento. Yo uso tres prefijos:

| Prefijo | Significado | Ejemplo |
| :---- | :---- | :---- |
| `personal-` | Skills personales, que no se comparten | `personal-daily-standup` |
| `team-` | Skills del equipo, con commit en el repo | `team-code-review-checklist` |
| `wip-` | Skills en desarrollo, todavía no estables | `wip-deploy-to-k8s` |

Las skills personales las tengo en un repositorio de dotfiles, con un enlace simbólico en lugar de la carpeta en `~/.claude/`:

```bash
# estructura en el repo de dotfiles:
#   dotfiles/claude/skills/personal-daily-standup/
#   dotfiles/claude/skills/personal-code-explain/
ln -s ~/dotfiles/claude/skills ~/.claude/skills
```

Si `~/.claude/skills` ya existe, mueve antes su contenido al repositorio; si no, `ln` crea el enlace dentro de la carpeta.

Las skills experimentales están fuera de las rutas que lee Claude Code, en `~/skills-wip/.claude/skills/`, donde no pesan en ninguna sesión. Para probar una, arranco `claude --add-dir ~/skills-wip`, que las carga solo para esa sesión. Cuando es estable, la muevo a su ubicación definitiva y le quito `wip-`.

### Cuánto cuestan

Cada skill te cuesta su description en cada sesión. Con tres skills no lo notas; con treinta, entre las tuyas y las de los plugins, ocupas una parte del contexto y aumentan las ocasiones de que se active la equivocada. Para las skills que lanzas solo tú, como un deploy, `disable-model-invocation: true` también saca la description del contexto: Claude ya no puede usarla por su cuenta, así que no necesita verla. Con `paths`, en cambio, limitas la activación automática a los archivos que importan, por ejemplo a los CSV de `data/`.

El peso de cada description lo ves en `/skills`. En el capítulo 15 usas `/skill-doctor`, que pone el coste en contexto junto a la frecuencia de uso y te dice qué skills compensan el espacio que ocupan.

### Cuando una skill no aparece

Si una skill recién creada no aparece en `/skills`, revisa por orden:

1. El archivo se llama exactamente `SKILL.md` y está un nivel por debajo de `skills/`, como en `.claude/skills/report-pdf/SKILL.md`.
2. El frontmatter es YAML válido: dos líneas `---`, espacios y no tabuladores, comillas cerradas.
3. `name` está en minúsculas con guiones, y conviene que coincida con el nombre de la carpeta: el estándar Agent Skills lo exige.
4. Has lanzado `/reload-skills` después de crear la carpeta.
5. No hay otra skill con el mismo nombre en un nivel distinto.

Si no encuentras el problema, pégale el archivo a Claude y descríbele qué pasa.

## Resumen {.unlisted}

- Comandos y skills son el mismo sistema: el archivo en `.claude/commands/` basta para un prompt, la carpeta `.claude/skills/<nombre>/` sirve para scripts, referencias y plantillas.
- De cada skill Claude ve siempre el nombre y la description; el cuerpo llega cuando la skill se activa, y los archivos de apoyo cuando las instrucciones los piden.
- La description decide si la skill se ejecuta: qué hace, sobre qué datos, con qué palabras la pedirá el usuario.
- Haz que los scripts calculen los números y los impriman, y en `SKILL.md` dile a Claude que no los rehaga a mano.
- El skill-creator, del marketplace oficial, escribe la skill y la compara con una ejecución sin ella.
- Las skills de dominio van en el proyecto y se suben con commit, las genéricas en `~/.claude/skills/`; `/skills` y `/skill-doctor` te dicen cuánto pesan.

## Ejercicio {.unlisted}

Elige un trabajo que repitas al menos una vez por semana: la revisión de un PR, el changelog de una release, los tests de una función nueva, la preparación de un entorno de desarrollo.

1. Instala el skill-creator y pídele que cree una skill para ese trabajo.
2. Responde a sus preguntas: qué hace, cuándo debe activarse, qué salida produce, qué casos límite conoces.
3. Acepta la verificación con los prompts de prueba y compara las salidas con y sin skill.
4. Abre el `SKILL.md` generado y relee la description: tiene que contener las palabras que usarías tú para pedir ese trabajo.
5. En un proyecto real, escribe una petición en lenguaje natural sin nombrar la skill.

El ejercicio está hecho cuando la skill aparece en `/skills`, se activa en el paso 5 sin que la nombres y, en la comparación del paso 3, el resultado con la skill es mejor que sin ella. Lleva una media hora.

Si quieres aclararte las ideas antes de abrir el skill-creator, parte del prompt de la carpeta `cap-08/` del repositorio `github.com/hidran/claude-code-book-snippets` (numeración de la primera edición): te hace fijar el nombre, el disparador y los pasos de la skill.
