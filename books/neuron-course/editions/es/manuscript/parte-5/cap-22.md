# Capítulo 22 — Workflows y aprobación humana en producción

## 22.1 El ciclo de vida de una aprobación

### La idea de la Sección 18.4, ampliada

Como las interrupciones son filas de Eloquent, «la IA está esperando a un humano» es un registro de tu base de datos. Lo que significa que recibe todo lo que reciben los registros de una base de datos: un estado, un propietario, un plazo, una página de índice, una policy, una traza de auditoría.

**El humano en el circuito deja de ser una funcionalidad de IA y se convierte en una funcionalidad de workflow de tu aplicación.** Ese cambio de encuadre es el objetivo de este capítulo.

### La tabla de apoyo

El `WorkflowInterrupt` del paquete guarda el estado de ejecución serializado. Tú quieres una tabla compañera que guarde la vista *de negocio*:

```php
Schema::create('pending_approvals', function (Blueprint $table) {
    $table->id();
    $table->string('workflow_id')->unique();
    $table->foreignId('tenant_id')->constrained();
    $table->foreignId('requested_by')->nullable()->constrained('users');
    $table->foreignId('resolved_by')->nullable()->constrained('users');

    $table->string('type');                 // refund, publish, escalation
    $table->string('subject_type')->nullable();
    $table->unsignedBigInteger('subject_id')->nullable();

    $table->json('request');                // the serialised InterruptRequest
    $table->json('response')->nullable();   // what the human decided

    $table->string('status')->default('pending');   // pending|approved|rejected|expired
    $table->timestamp('expires_at')->nullable();
    $table->timestamp('resolved_at')->nullable();

    $table->timestamps();

    $table->index(['tenant_id', 'status']);
    $table->index('expires_at');
});
```

**Por qué dos tablas.** La tabla del framework es un blob serializado: no puedes consultarla, filtrarla ni autorizar sobre ella. La tuya es un registro normal que puedes indexar, delimitar y renderizar. Separarlas significa que el framework es dueño de sus tripas y tú eres dueño de tu producto.

Vale la pena notar también que `subject_type` / `subject_id` es una relación polimórfica, así que una aprobación enlaza con el pedido, el artículo o la factura a la que se refiere. Sin ella, tu pantalla de aprobación muestra una carga JSON opaca y quien aprueba tiene que ir a buscar el registro por su cuenta.

### Los estados

```
pending ──aprobar──→ approved ──→ (workflow reanudado) ──→ completed
   │
   ├────rechazar───→ rejected ──→ (workflow reanudado con el rechazo)
   │
   └────timeout────→ expired ──→ (escalado o abandonado)
```

**El rechazo también reanuda el workflow.** Ese es el sentido del retorno de la Sección 15.2: el rechazo con realimentación es otra iteración, no un callejón sin salida.

### Las cuatro preguntas, respondidas

La Sección 15.4 las planteaba. Aquí van las respuestas de Laravel, que construye el resto de este capítulo:

| Pregunta | Respuesta |
|---|---|
| ¿A quién se notifica? | Una `Notification` enviada en el bloque catch (22.2) |
| ¿Y si nadie responde? | `expires_at` más un comando programado (22.4) |
| ¿Cómo evitar la doble reanudación? | `lockForUpdate()` sobre la columna de estado (22.3) |
| ¿Y los despliegues? | Peticiones de interrupción pequeñas, planas y rara vez modificadas (22.4) |

### Puntos clave

- Las interrupciones son filas, así que las aprobaciones son estado de aplicación corriente.
- Dos tablas: el blob serializado del framework y tu registro de negocio consultable.
- Relación polimórfica hacia el sujeto para que quien aprueba vea sobre qué está decidiendo.
- El rechazo reanuda el workflow; no es un estado terminal.

## 22.2 Capturar y notificar

### El bloque catch

```php
public function handle(): void
{
    $workflow = new RefundWorkflow(
        persistence: new EloquentPersistence(WorkflowInterrupt::class),
        workflowId: $this->workflowId,
    );

    try {
        $handler = $workflow->init();
        $handler->run();

        $this->recordCompletion($handler->getResult());

    } catch (WorkflowInterrupt $interrupt) {
        $approval = PendingApproval::create([
            'workflow_id'  => $interrupt->getWorkflowId(),
            'tenant_id'    => $this->tenantId,
            'type'         => 'refund',
            'subject_type' => Order::class,
            'subject_id'   => $this->orderId,
            'request'      => \json_encode($interrupt->getRequest()),
            'status'       => 'pending',
            'expires_at'   => now()->addHours(48),
        ]);

        Notification::send(
            $this->approversFor($approval),
            new ApprovalRequired($approval)
        );
    }
}
```

### A quién notificar

```php
private function approversFor(PendingApproval $approval): Collection
{
    return User::query()
        ->where('tenant_id', $approval->tenant_id)
        ->whereHas('roles', fn ($q) => $q->where('name', 'approver'))
        ->get();
}
```

Basado en roles, delimitado por tenant. Extiéndelo con umbrales —un reembolso de 50 € va a un supervisor, uno de 5.000 € a un responsable— usando el importe que ya está en la carga de la petición.

### La notificación

```php
class ApprovalRequired extends Notification implements ShouldQueue
{
    use Queueable;

    public function __construct(
        private readonly PendingApproval $approval,
    ) {}

    public function via(object $notifiable): array
    {
        return ['mail', 'database'];
    }

    public function toMail(object $notifiable): MailMessage
    {
        $request = \json_decode($this->approval->request, true);

        return (new MailMessage())
            ->subject("Approval needed: {$request['message']}")
            ->line($request['message'])
            ->action('Review', route('approvals.show', $this->approval))
            ->line('This request expires ' . $this->approval->expires_at->diffForHumans() . '.');
    }
}
```

### Dos puntos de diseño

**Incluye en el correo lo suficiente para decidir, pero decide en la aplicación.**

El asunto y el cuerpo deberían decirle a quien aprueba de qué va esto, para que pueda triar sin pinchar. La decisión en sí ocurre en una página autenticada, porque ahí es donde puedes autorizarla, bloquearla y auditarla.

Resiste los enlaces de aprobar/rechazar de un clic en el correo. Son cómodos, y son una superficie de seguridad de URLs firmadas que ahora te toca implementar bien.

**Indica la caducidad.** Quien aprueba sabiendo que la petición caduca en 48 horas se comporta de forma distinta a quien no lo sabe. Además hace visible en vez de sorprendente la política de tiempos de espera de la Sección 22.4.

### Puntos clave

- Crea el registro de negocio y notifica en el bloque catch.
- Enruta a quienes aprueban por rol, tenant y umbral.
- Correo para el aviso; la decisión en la aplicación autenticada.
- Dile a quien aprueba cuándo caduca.

## 22.3 La pantalla de aprobación y la reanudación segura

### El índice

```php
class ApprovalsController extends Controller
{
    public function index(Request $request)
    {
        $approvals = PendingApproval::query()
            ->where('tenant_id', $request->user()->tenant_id)
            ->where('status', 'pending')
            ->with('subject')
            ->latest()
            ->paginate(20);

        return view('approvals.index', compact('approvals'));
    }

    public function show(PendingApproval $approval)
    {
        $this->authorize('resolve', $approval);

        return view('approvals.show', [
            'approval' => $approval,
            'request'  => \json_decode($approval->request, true),
        ]);
    }
}
```

Una página de índice con una policy. Nada exótico, que es el objetivo.

### La acción de resolución, con el bloqueo

```php
public function resolve(Request $request, PendingApproval $approval)
{
    $this->authorize('resolve', $approval);

    $validated = $request->validate([
        'decision' => ['required', 'in:approve,reject'],
        'feedback' => ['nullable', 'string', 'max:2000'],
        'content'  => ['nullable', 'string'],   // for editable interrupts
    ]);

    $locked = DB::transaction(function () use ($approval, $validated, $request) {
        $fresh = PendingApproval::whereKey($approval->id)
            ->lockForUpdate()
            ->first();

        if ($fresh->status !== 'pending') {
            return null;   // someone else already decided
        }

        $fresh->update([
            'status'      => $validated['decision'] === 'approve' ? 'approved' : 'rejected',
            'response'    => \json_encode($validated),
            'resolved_by' => $request->user()->id,
            'resolved_at' => now(),
        ]);

        return $fresh;
    });

    if ($locked === null) {
        return back()->with('warning', 'This request was already resolved by someone else.');
    }

    ResumeWorkflow::dispatch($locked->workflow_id, $validated);

    return redirect()
        ->route('approvals.index')
        ->with('status', 'Decision recorded. The workflow is continuing.');
}
```

### Las tres cosas que esto hace bien

**`lockForUpdate()` dentro de una transacción.** Dos responsables abren el mismo correo y ambos pinchan aprobar. Sin el bloqueo, ambos envían un trabajo de reanudación y el workflow se ejecuta dos veces, lo que para un reembolso significa pagar dos veces.

**El estado se comprueba *después* de adquirir el bloqueo.** Comprobarlo antes es una condición de carrera; la comprobación debe ocurrir mientras se tiene el bloqueo.

**La reanudación se envía, no se ejecuta en línea.** El controlador registra una decisión y devuelve. Reanudar puede llevar un minuto; quien aprueba no debería esperarlo, y un tiempo de espera HTTP no debería dejar huérfano el workflow.

Ese tercer punto es fácil de saltarse y es la diferencia entre una pantalla que se siente instantánea y una que se queda colgada.

### El trabajo de reanudación

```php
class ResumeWorkflow implements ShouldQueue
{
    public int $tries = 1;

    public function __construct(
        public readonly string $workflowId,
        public readonly array $decision,
    ) {}

    public function handle(): void
    {
        $workflow = new RefundWorkflow(
            persistence: new EloquentPersistence(WorkflowInterrupt::class),
            workflowId: $this->workflowId,
        );

        $request = RefundApprovalInterrupt::fromArray($this->decision);

        $result = $workflow->init($request)->run();

        WorkflowCompleted::dispatch($this->workflowId, $result);
    }
}
```

Los tres requisitos de la Sección 15.4: misma persistencia, mismo ID de workflow, petición reconstruida.

### El caso editable

Para un `ContentReviewInterrupt` (Sección 15.3), la pantalla es un área de texto:

```blade
<form method="POST" action="{{ route('approvals.resolve', $approval) }}">
    @csrf

    <p class="mb-3">{{ $request['message'] }}</p>

    <textarea name="content" rows="20" class="w-full border rounded p-3">{{ $request['content'] }}</textarea>

    <div class="mt-4 flex gap-2">
        <button name="decision" value="approve" class="px-4 py-2 bg-black text-white rounded">
            Approve and publish
        </button>
        <button name="decision" value="reject" class="px-4 py-2 border rounded">
            Send back with feedback
        </button>
    </div>
</form>
```

El humano edita el contenido; la versión editada vuelve al workflow. El patrón de colaboración de la Sección 15.3, en un formulario. Es mucho más útil que aprobar/rechazar para cualquier cosa que la IA haya redactado, porque la respuesta común es «casi».

### Puntos clave

- `lockForUpdate()` en una transacción; comprueba el estado mientras tienes el bloqueo.
- Registra la decisión, envía la reanudación: nunca reanudes en línea.
- Misma persistencia, mismo ID, petición reconstruida.
- Para contenido redactado, un área de texto gana a dos botones.

## 22.4 Tiempos de espera, zombis y despliegues

### Hacer caducar las aprobaciones estancadas

```php
class ExpireStaleApprovals extends Command
{
    protected $signature = 'approvals:expire';

    public function handle(): int
    {
        PendingApproval::query()
            ->where('status', 'pending')
            ->where('expires_at', '<', now())
            ->chunkById(100, function ($approvals) {
                foreach ($approvals as $approval) {
                    $approval->update([
                        'status'      => 'expired',
                        'resolved_at' => now(),
                    ]);

                    ResumeWorkflow::dispatch($approval->workflow_id, [
                        'decision' => 'reject',
                        'feedback' => 'No response received within the approval window.',
                    ]);
                }
            });

        return self::SUCCESS;
    }
}
```

**Reanuda con un rechazo en lugar de abandonar.** Un workflow abandonado deja su estado serializado en la base de datos para siempre y no le cuenta a nadie qué pasó. Uno rechazado se completa, notifica y limpia.

Prográmalo:

```php
Schedule::command('approvals:expire')->hourly();
```

### Escalado antes de la caducidad

Mejor comportamiento de producto que un tiempo de espera silencioso:

```php
Schedule::call(function () {
    PendingApproval::where('status', 'pending')
        ->where('created_at', '<', now()->subHours(24))
        ->whereNull('escalated_at')
        ->each(function ($approval) {
            Notification::send($approval->escalationTargets(), new ApprovalOverdue($approval));
            $approval->update(['escalated_at' => now()]);
        });
})->hourly();
```

Un recordatorio a las 24 horas, caducidad a las 48.

### Filas de interrupción huérfanas

La tabla `workflow_interrupts` del framework crece. Limpia las filas cuyo registro de negocio está resuelto:

```php
WorkflowInterrupt::query()
    ->whereNotIn('workflow_id', function ($q) {
        $q->select('workflow_id')
          ->from('pending_approvals')
          ->where('status', 'pending');
    })
    ->where('updated_at', '<', now()->subDays(30))
    ->delete();
```

Treinta días de gracia y luego se eliminan. Sin esto, un sistema con actividad acumula blobs serializados indefinidamente.

### El problema de los despliegues, y cómo convivir con él

La Sección 15.4 lo señalaba; aquí va la gestión práctica.

El estado serializado contiene **tus clases**. Renombra un nodo, añade una property tipada a una clase de estado, cambia el constructor de una petición de interrupción, y la deserialización de los workflows en vuelo se rompe.

Cuatro mitigaciones, en orden de utilidad:

**1. Mantén las peticiones de interrupción pequeñas y planas.** Cadenas, números, arrays. Sin modelos, sin conexiones, sin closures. Cuanto menor sea la superficie, menos hay que romper.

**2. Versiónalas.**

```php
class RefundApprovalInterrupt extends InterruptRequest
{
    public const VERSION = 2;

    public function jsonSerialize(): array
    {
        return [
            'version' => self::VERSION,
            'message' => $this->message,
            'amount'  => $this->amount,
        ];
    }

    public static function fromArray(array $data): static
    {
        return match ($data['version'] ?? 1) {
            1       => new static($data['message'], (float) $data['amount']),
            default => new static($data['message'], (float) $data['amount']),
        };
    }
}
```

**3. Vacía antes de los despliegues arriesgados.** Para una versión que cambie clases de workflow, deja de enviar workflows nuevos, deja que se resuelvan los pendientes y luego despliega.

**4. Falla ruidosamente.** Envuelve la reanudación en un try/catch, registra el fallo de deserialización con el ID de workflow y marca la aprobación como `failed` en lugar de dejarla pendiente para siempre. Un fallo visible es recuperable; uno silencioso no.

### Monitorización

Cuatro números que merecen un panel:

- Aprobaciones pendientes, por antigüedad
- Aprobaciones caducadas en los últimos 7 días: un número creciente significa que lo que está roto es tu proceso, no tu código
- Reanudaciones fallidas
- Filas de interrupción huérfanas

### Puntos clave

- Haz caducar reanudando con un rechazo, nunca abandonando.
- Escala antes de hacer caducar.
- Limpia las filas de interrupción huérfanas tras un periodo de gracia.
- El estado serializado contiene tus clases: mantén las peticiones planas, versiónalas, vacía antes de los despliegues arriesgados.
- Falla ruidosamente ante los errores de deserialización.

## Laboratorio 16 — Aprobación de reembolsos, de principio a fin

**Cubre:** toda la Parte IV y toda la Parte V. Este es el laboratorio que demuestra que el patrón es desplegable.

### Objetivo

Un agente prepara un reembolso. El workflow se detiene. Un responsable aprueba desde una pantalla autenticada. El workflow se reanuda en un worker y ejecuta el reembolso, sobreviviendo entretanto a un reinicio de proceso y a un despliegue.

### El flujo

```
El cliente pide un reembolso
   ↓
El agente reúne el pedido, comprueba la elegibilidad, prepara el caso   (con checkpoint)
   ↓
¿Reembolso por encima de 100 €?  → interrupción
   ↓
Fila PendingApproval + notificación a quienes aprueban
   ↓                                      (pasan las horas; nada se está ejecutando)
El responsable abre la pantalla de aprobación, ve el pedido y el caso
   ↓
Aprueba (con un importe ajustado opcional) o rechaza con realimentación
   ↓
Trabajo ResumeWorkflow → reembolso ejecutado → fila de auditoría → cliente notificado
```

### Requisitos

1. **Pon checkpoints en todo antes de la interrupción.** Sección 15.5. El caso que lee el responsable debe ser el caso sobre el que actúa el workflow.
2. **`interruptIf()`** para que los reembolsos por debajo de 100 € nunca interrumpan.
3. **Un registro `pending_approvals`** con relación polimórfica al `Order`, para que la pantalla muestre sobre qué se está decidiendo.
4. **`lockForUpdate()`** al resolver, con el estado comprobado dentro del bloqueo.
5. **Reanudación enviada, no en línea.**
6. **`expires_at` a 48 horas**, escalado a 24, ambos programados.
7. **Una fila de auditoría** para el reembolso, que nombre a quien aprobó.

### Criterios de aceptación

- Un reembolso de 40 € se completa sin intervención humana.
- Un reembolso de 400 € crea una aprobación, notifica, y nada se ejecuta hasta que se resuelve.
- Dos pestañas del navegador pinchando ambas aprobar producen **un** reembolso y un mensaje de «ya resuelta» en la segunda.
- Reiniciar el worker de cola y el servidor de aplicación entre la interrupción y la reanudación no cambia nada.
- El importe de la fila de auditoría coincide con el importe que vio quien aprobó. Demuéstralo registrando dentro de la closure del checkpoint y confirmando que se ejecutó una sola vez.
- Una aprobación dejada 48 horas caduca, se reanuda con un rechazo y notifica al cliente, en lugar de quedarse pendiente para siempre.

### Los dos modos de fallo que reproducir deliberadamente

**Doble reanudación.** Quita el bloqueo, pincha aprobar en dos pestañas y observa aparecer dos reembolsos. Vuelve a ponerlo.

**Regeneración sin checkpoint.** Quita el `checkpoint()` de la preparación del caso y confirma que la ejecución reanudada produce un caso distinto del aprobado. En un workflow de reembolsos eso no es una ineficiencia: es aprobar un importe y pagar otro.

Ambos son experimentos de cinco minutos, y ambos convencen más que cualquier cantidad de prosa sobre por qué existen esas salvaguardas.

### Ir más allá

Añade una simulación de despliegue: interrumpe un workflow, añade una property tipada a tu clase de petición de interrupción, despliega e intenta la reanudación. Míralo fallar. Después aplica el versionado de la Sección 22.4 y míralo funcionar. Ese es el ejercicio que convierte «mantén planas las peticiones de interrupción» de consejo en una regla que seguirás de verdad.
