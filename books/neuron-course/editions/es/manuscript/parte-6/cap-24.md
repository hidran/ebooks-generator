# Capítulo 24 — Proyecto final A: la CLI auditora de repositorios

**Stack:** PHP puro + Composer. Sin framework.
**Cubre:** los Capítulos 3 al 10, toda la Parte II.

Este proyecto final está especificado, no resuelto. Enuncia requisitos y criterios de aceptación y te deja el diseño a ti.

## Qué vas a construir

Un agente de línea de comandos que audita un repositorio PHP y produce un informe estructurado:

```bash
php auditor.php /path/to/repo --format=json
```

```
Auditing /home/hidran/projects/shop ...

  Reading composer.json
  Scanning source tree (412 files)
  Checking dependency advisories
  Reading recent commit history
  Analysing test coverage configuration

━━━ Repo Audit: shop ━━━

Health score       62 / 100
PHP constraint     ^8.1  (consider ^8.3)
Dependencies       47 direct, 3 with known advisories
Test setup         PHPUnit present, no coverage threshold configured
Commit cadence     14 commits in the last 30 days, 2 contributors

Findings (7)
  [high]   Package X has advisory CVE-... — upgrade to 2.4.1
  [medium] No CI configuration found
  [medium] 23 files exceed 400 lines
  ...

Written to audit-shop-2026-08-10.json
```

## Por qué este proyecto

**No tiene dependencias externas.** Sin claves de API más allá del LLM, sin base de datos, sin servicios. Puedes completarlo en un portátil, sin conexión, con Ollama.

**Las tools son genuinamente útiles.** Leer archivos, ejecutar `git log`, parsear `composer.json`: estas son las formas de tool que necesitan la mayoría de los agentes reales.

**Ejercita toda la superficie de la Parte II** sin nada de conocimiento de Laravel, lo que lo convierte en una pieza de portafolio autónoma si trabajas en Symfony, WordPress o un stack heredado.

## Orden de construcción

### Fase 1 — Andamiaje y el primer agente

- Configuración del proyecto de la Sección 3.1
- `ProviderFactory` de la Sección 3.6
- `AuditorAgent` con un `SystemPrompt` que lo establece como auditor de código, no como reparador de código
- Un punto de entrada de CLI que reciba un argumento de ruta

### Fase 2 — Las tools del sistema de archivos

Engancha `FileSystemToolkit` con `only()`, y escribe dos tools propias:

```php
class ComposerManifestTool extends Tool
{
    public function __construct(private readonly string $repoPath)
    {
        parent::__construct(
            'read_composer_manifest',
            'Returns the composer.json of the repository being audited: the PHP version '
            . 'constraint, the direct dependencies with their version constraints, the '
            . 'autoload configuration, and the declared scripts. Use this first, before any '
            . 'other analysis, to understand what kind of project this is. Never guess a '
            . 'dependency version — read it here.'
        );
    }

    protected function properties(): array
    {
        return [];   // no arguments — the path is a constructor dependency
    }

    public function __invoke(): string
    {
        $path = $this->repoPath . '/composer.json';

        if (! \is_file($path)) {
            return 'No composer.json found. This may not be a PHP project.';
        }

        $manifest = \json_decode(\file_get_contents($path), true, 512, JSON_THROW_ON_ERROR);

        return \json_encode([
            'name'        => $manifest['name']      ?? null,
            'php'         => $manifest['require']['php'] ?? null,
            'require'     => $manifest['require']     ?? [],
            'require-dev' => $manifest['require-dev'] ?? [],
            'scripts'     => \array_keys($manifest['scripts'] ?? []),
        ], JSON_THROW_ON_ERROR);
    }
}
```

**Dos cosas que notar.**

La tool no tiene **ninguna property**: la ruta del repositorio es una dependencia del constructor, no algo que elija el modelo. Es deliberado: una ruta suministrada por el modelo es un path traversal esperando a ocurrir. El principio de la Sección 5.1, aplicado en concreto.

El valor de retorno es un manifiesto **reducido**, no el archivo entero. El argumento sobre el coste en tokens de la Sección 19.1, en un contexto de PHP puro.

### Fase 3 — La tool de git y la ejecución segura de subprocesos

```php
class GitHistoryTool extends Tool
{
    public function __construct(private readonly string $repoPath) { /* ... */ }

    protected function properties(): array
    {
        return [
            new ToolProperty(
                name: 'days',
                type: PropertyType::NUMBER,
                description: 'How many days of history to summarise. Example: 30. Maximum 365.',
                required: true,
            ),
        ];
    }

    public function __invoke(int $days): string
    {
        $days = \max(1, \min(365, $days));   // clamp, never trust the model

        $process = new Process(
            ['git', 'log', "--since={$days} days ago", '--pretty=format:%h|%an|%ad|%s', '--date=short'],
            $this->repoPath,
        );

        $process->setTimeout(15);
        $process->run();

        if (! $process->isSuccessful()) {
            return 'Could not read git history. This may not be a git repository.';
        }

        $lines = \array_slice(\explode("\n", \trim($process->getOutput())), 0, 100);

        return $lines === [''] ? 'No commits in this period.' : \implode("\n", $lines);
    }
}
```

**Tres cosas que esto hace bien, y todas importan:**

**Arrays de argumentos, nunca interpolación de cadenas.** `['git', 'log', "--since={$days} days ago"]` con Symfony Process pasa los argumentos sin shell. Interpolar un valor suministrado por el modelo dentro de una cadena de shell es ejecución remota de código con pasos extra.

**Acota la entrada numérica.** `max(1, min(365, $days))`. El modelo puede enviar 99999. Los atributos de validación son para el structured output; los argumentos de tools los validas tú.

**Acota la salida.** `array_slice(..., 0, 100)`. Un repositorio con 40.000 commits pondría si no 40.000 líneas en la conversación.

### Fase 4 — Structured output

El DTO `AuditReport`, usando todo lo del Capítulo 6:

```php
class Finding
{
    #[SchemaProperty(description: 'Severity: one of high, medium, low.', required: true)]
    #[Regex('/^(high|medium|low)$/')]
    public string $severity;

    #[SchemaProperty(description: 'Category, e.g. dependencies, testing, structure, security.', required: true)]
    #[NotBlank]
    public string $category;

    #[SchemaProperty(description: 'What the issue is, in one sentence. State the fact you observed.', required: true)]
    #[WordsCount(max: 30)]
    public string $description;

    #[SchemaProperty(description: 'The concrete action to take. Start with a verb.', required: true)]
    #[WordsCount(max: 25)]
    public string $recommendation;

    #[SchemaProperty(description: 'The file or package this concerns, if applicable.', required: false)]
    public ?string $subject = null;
}
```

```php
class AuditReport
{
    #[SchemaProperty(description: 'Overall health score from 0 to 100.', required: true)]
    #[GreaterThanEqual(reference: 0)]
    #[LowerThanEqual(reference: 100)]
    public int $score;

    #[SchemaProperty(description: 'Two-sentence summary of the repository state.', required: true)]
    #[WordsCount(min: 15, max: 60)]
    public string $summary;

    #[SchemaProperty(
        description: 'Every issue found, most severe first.',
        required: true,
        anyOf: [Finding::class]
    )]
    public array $findings;
}
```

Aquí `#[WordsCount]` hace trabajo real: sin él, el modelo escribe párrafos donde querías una línea, y la salida de tu terminal se vuelve ilegible.

### Fase 5 — Streaming, gestión de errores y límites de ejecución

- `stream()` con etiquetas de actividad de tools (Sección 7.4)
- `toolErrorHandler()` que devuelve instrucciones (Sección 5.11)
- `toolMaxRuns()` ajustado por tool: manifiesto 1, sistema de archivos 15, git 3
- Gestiona SIGINT con elegancia: esta es una herramienta de CLI, así que `connection_aborted()` no aplica, pero un usuario que pulsa Ctrl-C merece igualmente una salida limpia

### Fase 6 — Traces, evaluaciones y empaquetado

- Habilita Inspector, lee un trace real y ajusta las descripciones de las tools según lo que veas
- Una pequeña suite de evaluación: cinco repositorios con problemas conocidos, con asertos de que los hallazgos los mencionen
- Empaquétalo como `bin` de Composer para que se instale globalmente

## Rúbrica de evaluación

| Criterio | Evidencia |
|---|---|
| Diseño de tools | Las descripciones siguen la fórmula en cuatro partes; las descripciones de properties contienen ejemplos |
| Seguridad | Ninguna ruta suministrada por el modelo; argumentos de proceso como arrays; entradas numéricas acotadas |
| Disciplina de tokens | Toda tool acota y reduce su salida |
| Estructura | El informe es un DTO validado, no prosa parseada |
| Resiliencia | El handler de errores devuelve instrucciones; límites de ejecución fijados por tool |
| Medición | Existe una suite de evaluación que produce una puntuación |

## Criterios de aceptación

- El auditor se ejecuta sobre tres repositorios de formas genuinamente distintas —una app Laravel, una biblioteca, algo heredado— sin excepciones.
- Un repositorio sin `composer.json` produce un mensaje útil, no una caída.
- Un repositorio sin historial de git produce un mensaje útil, no una caída.
- El informe valida al primer intento en al menos dos de los tres, y el reintento es visible en el trace cuando no lo hace.
- Ejecutar el mismo repositorio dos veces produce informes que difieren en la redacción y coinciden en los hallazgos. Si no coinciden en los hallazgos, lo que hay que trabajar son las descripciones de tus tools, no tu prompt.

Ese último criterio es el interesante. Es el no determinismo de la Sección 1.5, medido sobre tu propia salida, y es la diferencia entre una herramienta en la que confiarías y un juguete.

## Extensiones

1. Añade `parallelToolCalls(true)`: esta es una herramienta de CLI, así que `pcntl` está disponible (Sección 5.13). Mide la diferencia de tiempo de reloj en un repositorio grande.
2. Añade un conector MCP a un servidor de GitHub para el contexto de issues y pull requests (Capítulo 9). Aplica la clasificación por niveles de confianza de la Sección 9.4 antes de hacerlo.
3. Ejecuta la auditoría con tres providers y publica las diferencias. ¿Qué hallazgos aparecen en los tres? Esos son en los que puedes confiar.
