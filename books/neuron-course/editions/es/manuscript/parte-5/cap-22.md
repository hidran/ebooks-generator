# Capítulo 22 — Flujos de trabajo y aprobación humana en producción

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

Los listados de Laravel de abajo viven dentro de una aplicación, pero el flujo de trabajo que conducen es ejecutable por sí solo en [`chapters/Ch22`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch22) del repositorio complementario. `refund.php` recorre el ciclo de vida completo (el reembolso aprobado automáticamente, la pausa, la reanudación con barrera, la reentrega rechazada, el plazo vencido y la finalización retenida) sin modelo y sin Laravel. `agent-approval.php` reproduce de la misma forma el ciclo completo de aprobación de un agente de la Sección 22.5, con un agente nuevo por petición, reconstruido solo a partir del ID de hilo.
:::

## 22.1 El ciclo de vida de una aprobación

### La idea de la Sección 18.4, ampliada

Como una ejecución suspendida vive en tu base de datos, «la IA está esperando a un humano» es un hecho que tu aplicación puede guardar como registro. Lo que significa que recibe todo lo que reciben los registros de una base de datos: un estado, un propietario, un plazo, una página de índice, una policy, una traza de auditoría.

**El humano en el circuito deja de ser una funcionalidad de IA y se convierte en una funcionalidad de flujo de trabajo de tu aplicación.** Ese cambio de encuadre es el objetivo de este capítulo.

### La tabla de apoyo

La tabla `workflow_store` del framework guarda la ejecución en sí: su registro de control, sus pasos completados, su estado suspendido, la petición pendiente. Tú quieres una tabla compañera que guarde la vista *de negocio*:

```php
Schema::create('pending_approvals', function (Blueprint $table) {
    $table->id();
    $table->string('workflow_id');          // the continuation handle, e.g. refund:1042
    $table->string('run_id');               // the generation that asked
    $table->unsignedInteger('interrupt_id');        // which of that run's pauses
    $table->unsignedInteger('execution_attempt');   // the attempt that paused
    $table->foreignId('tenant_id')->constrained();
    $table->foreignId('requested_by')->nullable()->constrained('users');
    $table->foreignId('resolved_by')->nullable()->constrained('users');

    $table->string('type');                 // refund, publish, escalation
    $table->string('subject_type')->nullable();
    $table->unsignedBigInteger('subject_id')->nullable();

    $table->json('request');                // the InterruptRequest, as JSON, for rendering
    $table->json('response')->nullable();   // what the human decided

    $table->string('status')->default('pending');   // pending|approved|rejected|expired|failed
    $table->timestamp('expires_at')->nullable();
    $table->timestamp('resolved_at')->nullable();

    $table->timestamps();

    $table->unique(['workflow_id', 'run_id', 'interrupt_id']);
    $table->index(['tenant_id', 'status']);
    $table->index('expires_at');
});
```

**Por qué dos tablas.** La tabla del framework es un conjunto de registros serializados opacos indexados por partición: no puedes consultarla, filtrarla ni autorizar sobre ella, y no deberías intentarlo, porque sus filas cambian bajo escrituras condicionales que no controlas. La tuya es un registro normal que puedes indexar, delimitar y renderizar. Separarlas significa que el framework es dueño de sus tripas y tú eres dueño de tu producto.

**Lo que copias es una proyección, no la petición.** La persistencia del flujo de trabajo sigue siendo la fuente autorizada de la petición pendiente. Tu tabla guarda lo que necesita para encaminar la respuesta (el ID del flujo de trabajo, el ID de ejecución, el ID de interrupción y el intento de ejecución que observó) más una representación JSON de la petición para la pantalla. El ID de ejecución y el intento son las barreras de entrega de la Sección 22.3; sin ellos, una respuesta tardía o duplicada no se puede distinguir de una actual. El ID de interrupción está ahí porque una misma ejecución puede pausarse más de una vez (un rechazo que vuelve atrás, un nodo que espera dos veces) y cada pausa tiene su propia fila; una clave única sin él rechazaría la segunda.

Vale la pena notar también que `subject_type` / `subject_id` es una relación polimórfica, así que una aprobación enlaza con el pedido, el artículo o la factura a la que se refiere. Sin ella, tu pantalla de aprobación muestra una carga JSON opaca y quien aprueba tiene que ir a buscar el registro por su cuenta.

### Los estados

```
pending ──aprobar──→ approved ──→ (flujo de trabajo reanudado) ──→ completed
   │
   ├────rechazar───→ rejected ──→ (flujo de trabajo reanudado con el rechazo)
   │
   └────vencer─────→ expired ──→ (flujo de trabajo reanudado sin respuesta; el nodo toma su rama de tiempo agotado)
```

**Todos los caminos reanudan el flujo de trabajo.** La aprobación lo hace continuar, el rechazo es otra iteración (el retorno de la Sección 15.2) y una caducidad es el flujo de trabajo dándose cuenta de su propio plazo. Ninguno es un callejón sin salida que deje atrás una ejecución suspendida.

### Las cuatro preguntas, respondidas

La Sección 15.4 las planteaba. Aquí van las respuestas de Laravel, que construye el resto de este capítulo:

| Pregunta | Respuesta |
|---|---|
| ¿A quién se notifica? | Una `Notification` enviada cuando la ejecución vuelve interrumpida (22.2) |
| ¿Y si nadie responde? | `expiresAt` en la petición, más una reanudación sin entrada programada (22.4) |
| ¿Cómo evitar la doble reanudación? | Las escrituras condicionales y las barreras de entrega del motor, más `lockForUpdate()` sobre tu registro (22.3) |
| ¿Y los despliegues? | Peticiones de interrupción pequeñas, planas, rara vez modificadas y con propiedades con valor por defecto (22.4) |

### Puntos clave

- Una ejecución suspendida es un hecho de la base de datos, así que las aprobaciones son estado de aplicación corriente.
- Dos tablas: el almacén opaco del framework y tu registro de negocio consultable.
- Copia una proyección (ID del flujo de trabajo, ID de ejecución, ID de interrupción, intento); nunca trates tu copia como la fuente de verdad.
- Relación polimórfica hacia el sujeto para que quien aprueba vea sobre qué está decidiendo.
- Todo resultado, incluida la caducidad, reanuda el flujo de trabajo.

## 22.2 Detectar la pausa y notificar

### El trabajo que inicia la ejecución

```php
public function handle(PersistenceInterface $runs): void
{
    try {
        $state = RefundWorkflow::make(orderId: $this->orderId, requestedAmount: $this->amount)
            ->setPersistence($runs)
            ->setLeaseTimeout(600)
            // Minted with the request: every delivery of this job names the same run.
            ->run(ExecutionRequest::start(runId: $this->runId, recoverFailed: true));
    } catch (RunInFlightException $e) {
        if ($e->reservedRunId !== $e->runId) {
            // One live run per workflow ID: another request's refund holds this order.
            $this->recordDuplicateRequest($e->status);
        } elseif ($e->status === WorkflowStatus::Suspended) {
            // An earlier delivery paused this run and died before it recorded the pause.
            $this->recordPause($e->workflowId, $e->runId, $e->executionAttempt, $e->interrupt);
        } else {
            // A killed delivery still holds the lease: come back when it has expired.
            $this->release(\max(1, $e->leaseExpiresAt - \time()));
        }

        return;
    }

    if (! $state->isInterrupted()) {
        $this->recordCompletion($state);

        return;
    }

    $this->recordPause(
        $state->getWorkflowId(),
        $state->getRunId(),
        $state->getExecutionAttempt(),
        $state->getInterruptRequest(),
    );
}

private function recordPause(
    string $workflowId,
    string $runId,
    int $attempt,
    InterruptRequest $request,
): void {
    // Repeatable: a redelivery finds the row, and nobody is notified twice.
    $approval = PendingApproval::firstOrCreate([
        'workflow_id'  => $workflowId,
        'run_id'       => $runId,
        'interrupt_id' => $request->getId(),
    ], [
        'execution_attempt' => $attempt,
        'tenant_id'         => $this->tenantId,
        'type'              => 'refund',
        'subject_type'      => Order::class,
        'subject_id'        => $this->orderId,
        'request'           => \json_encode($request),
        'status'            => 'pending',
        'expires_at'        => $request instanceof RefundApprovalRequest ? $request->getExpiresAt() : null,
    ]);

    if ($approval->wasRecentlyCreated) {
        Notification::send(
            $this->approversFor($approval),
            new ApprovalRequired($approval)
        );
    }
}
```

No se captura nada para la pausa. `run()` vuelve con normalidad, y el estado dice si la ejecución terminó o está esperando. La pausa es un resultado, no una excepción (Sección 15.1), y por eso el registro de negocio y la notificación cuelgan de un `if` corriente.

**El ID de ejecución se reserva, no se genera.** Lo acuña el controlador que acepta la petición de reembolso (`(string) Str::uuid()`) y se lo pasa al trabajo junto con el pedido y el importe, de modo que cada entrega de ese trabajo nombra la misma ejecución. `ExecutionRequest::start(runId: ..., recoverFailed: true)` dice entonces lo mismo cada vez: inicia esta ejecución o, si una entrega anterior la dejó fallida o mataron a su proceso, termínala desde el último paso confirmado. Un `run()` sencillo no puede decirlo. Recupera cualquier ejecución fallida que encuentre bajo el ID del flujo de trabajo, así que una segunda petición para un pedido cuyo primer reembolso falló a medias terminaría en silencio la *primera* petición (su importe, su caso) y la daría por la segunda.

La única excepción que vale la pena capturar es `RunInFlightException`. `RefundWorkflow` declara `refund:{orderId}` como su ID del flujo de trabajo (Sección 15.4), y un inicio reservado nunca sustituye una ejecución que no inició, así que una segunda petición de reembolso para un pedido cuyo primer reembolso sigue esperando aprobación (o falló y espera a ser recuperado) se rechaza antes de que se ejecute nada. Es una regla de negocio que obtienes gratis; conviértela en un mensaje en lugar de en un trabajo fallido. `reservedRunId` distingue ese caso de los otros dos, en los que la ejecución que estorba es del propio trabajo. Si se la encuentra suspendida, la pausó una entrega anterior que murió antes de registrar la pausa: la excepción lleva el ID de ejecución, el intento y la petición, que es todo lo que el registro necesita. Si se la encuentra todavía en ejecución, el trabajo vuelve a la cola hasta que la concesión haya vencido.

`recordPause()` está escrito para poder repetirse: `firstOrCreate()` sobre la clave única de la tabla hace que una reentrega encuentre la fila que escribió una entrega anterior, y solo la entrega que la creó notifica. La persistencia es la vinculación del Capítulo 18 (`DatabasePersistence` sobre la propia conexión de Laravel), inyectada en `handle()`. La concesión, y los `$tries = 3` y `$timeout = 300` que este trabajo declara igual que el siguiente, se explican en las Secciones 22.3 y 22.4.

El plazo viene de la petición. `RefundApprovalRequest` es una subclase de `WaitForEventRequest` (Sección 15.3), y el nodo que la lanza fija `expiresAt`, de modo que las 48 horas viven en un solo sitio, el flujo de trabajo, y tu tabla se limita a reflejarlas para indexarlas.

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

Basado en roles, delimitado por inquilino. Extiéndelo con umbrales —un reembolso de 50 € va a un supervisor, uno de 5.000 € a un responsable— usando el importe que ya está en la carga de la petición.

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

`$request['message']` está ahí porque lo pone `RefundApprovalRequest::metadata()`. La forma JSON de una petición son los campos del framework (`interruptId`, `type`, `eventName`, `expiresAt`) seguidos de lo que añada tu subclase; diseña `metadata()` pensando en la pantalla y el correo, ya que son sus únicos lectores.

### Dos puntos de diseño

**Incluye en el correo lo suficiente para decidir, pero decide en la aplicación.**

El asunto y el cuerpo deberían decirle a quien aprueba de qué va esto, para que pueda triar sin pinchar. La decisión en sí ocurre en una página autenticada, porque ahí es donde puedes autorizarla, bloquearla y auditarla.

Resiste los enlaces de aprobar/rechazar de un clic en el correo. Son cómodos, y son una superficie de seguridad de URLs firmadas que ahora te toca implementar bien.

**Indica la caducidad.** Quien aprueba sabiendo que la petición caduca en 48 horas se comporta de forma distinta a quien no lo sabe. Además hace visible en vez de sorprendente la política de tiempos de espera de la Sección 22.4.

### Puntos clave

- `run()` vuelve; si `isInterrupted()`, registra la proyección y notifica.
- Empieza con un ID de ejecución reservado por la petición y con `recoverFailed: true`, nunca con un `run()` sencillo.
- Captura `RunInFlightException`: una sola ejecución viva por ID del flujo de trabajo es una regla de negocio, y `reservedRunId` distingue una segunda petición de una reentrega.
- El plazo vive en la petición; tu tabla lo refleja.
- Enruta a quienes aprueban por rol, inquilino y umbral.
- Correo para el aviso; la decisión en la aplicación autenticada.

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
        Gate::authorize('resolve', $approval);

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
    Gate::authorize('resolve', $approval);

    $requested = \json_decode($approval->request, true)['amount'];

    $validated = $request->validate([
        'decision' => ['required', 'in:approve,reject'],
        'feedback' => ['nullable', 'string', 'max:2000'],
        // The approver may lower the amount, never raise it.
        'amount'   => ['nullable', 'numeric', 'min:0', "max:{$requested}"],
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

    ResumeRefundWorkflow::dispatch($locked, $validated);

    return redirect()
        ->route('approvals.index')
        ->with('status', 'Decision recorded. The workflow is continuing.');
}
```

### Dos capas, dos trabajos

Dos responsables abren el mismo correo y ambos pinchan aprobar. Hay dos cosas que no deben ocurrir: el reembolso no debe pagarse dos veces, y tus registros no deben decir que lo aprobaron dos personas.

**De la primera se encarga el motor.** Cada modificación de una ejecución es una escritura condicional sobre su registro de control, así que solo se puede aceptar una continuación. Una segunda reanudación de una ejecución terminada no encuentra nada en curso; una que compita con la primera pierde la escritura. Para un reembolso es la diferencia entre pagar una vez y pagar dos, y se mantiene aunque tu propio código haga mal el bloqueo.

**De la segunda se encarga tu bloqueo.** `lockForUpdate()` dentro de una transacción, con el estado comprobado *después* de adquirir el bloqueo: comprobarlo antes es una condición de carrera. Sin él, el motor sigue pagando una sola vez, pero ambos responsables ven «decisión registrada», ambos quedan guardados como quien aprobó y la traza de auditoría miente. El bloqueo es lo que convierte el segundo clic en «ya resuelta por otra persona».

**La reanudación se envía, no se ejecuta en línea.** El controlador registra una decisión y devuelve. Reanudar puede llevar un minuto; quien aprueba no debería esperarlo, y un tiempo de espera HTTP no debería dejar huérfano el flujo de trabajo.

Ese tercer punto es fácil de saltarse y es la diferencia entre una pantalla que se siente instantánea y una que se queda colgada.

### El trabajo de reanudación

```php
class ResumeRefundWorkflow implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;

    /** Longer than the longest continuation, shorter than the queue's retry_after (360). */
    public int $timeout = 300;

    public function __construct(
        public readonly PendingApproval $approval,
        public readonly ?array $decision,   // null: deliver nothing, let the workflow check its deadline
    ) {}

    public function handle(PersistenceInterface $runs): void
    {
        $workflow = RefundWorkflow::make(orderId: $this->approval->subject_id)
            ->setPersistence($runs)
            ->setLeaseTimeout(600);

        try {
            $state = $workflow->run($this->request($workflow->inspect()));
        } catch (StaleWorkflowRunException $e) {
            // The run this answer was meant for is gone or replaced. Nothing was touched.
            Log::info('Stale refund resume ignored', ['approval' => $this->approval->id]);

            return;
        }

        if ($state->isInterrupted()) {
            return;   // still waiting: the deadline is not due yet
        }

        $this->recordOutcome($state);   // audit row, customer notification
    }

    private function request(?WorkflowRunSnapshot $run): ExecutionRequest
    {
        $runId = $this->approval->run_id;

        // A redelivery: the answer is already in and a later step failed. Finish that run.
        if ($run?->runId === $runId && $run->status === WorkflowStatus::Failed) {
            return ExecutionRequest::resume(
                expectedRunId: $runId,
                expectedExecutionAttempt: $run->executionAttempt,   // the attempt it is on now
            );
        }

        $fences = [
            'expectedRunId'            => $runId,
            'expectedExecutionAttempt' => $this->approval->execution_attempt,
        ];

        if ($this->decision === null) {
            // Nothing to deliver: the workflow checks its own deadline.
            return ExecutionRequest::resume(...$fences);
        }

        return ExecutionRequest::signal(
            RefundApprovalRequest::EVENT,
            $this->decision,
            ...$fences,
        );
    }
}
```

Los requisitos de la Sección 15.4, ahora en un trabajo de cola: **la misma clase de flujo de trabajo**, reconstruida solo a partir del ID del pedido porque la clase declara `refund:{orderId}` como su ID del flujo de trabajo; **la misma persistencia**; y **la carga**, un array sencillo que el nodo lee directamente. No hay ninguna petición de interrupción que reconstruir.

Lo que añade el trabajo es la pareja de **barreras**. `expectedRunId` y `expectedExecutionAttempt` son los valores que la ejecución comunicó al pausarse, y el motor se niega a entregar la respuesta si la ejecución ha avanzado desde entonces: una nueva generación bajo el mismo ID del flujo de trabajo, u otro proceso que ya la continuó. Las colas reentregan, los usuarios hacen doble clic, los despliegues reinician procesos a mitad de un trabajo: las barreras convierten cada uno de esos casos en una negativa en lugar de en una respuesta aplicada a la petición equivocada.

**La primera rama de `request()` es la que consigue que los reembolsos se paguen.** El trabajo se reintenta (`$tries = 3`) porque una continuación se puede ejecutar de nuevo sin riesgo: los pasos completados se reproducen desde el almacén, no se ejecutan (Sección 13.5). Pero un reintento no puede limitarse a repetirse. Una vez que el motor ha aceptado la respuesta, la ejecución está en un intento posterior, y si un paso posterior lanza entonces una excepción (la API de pago está caída), la ejecución queda `failed` y el intento de tu tabla está obsoleto para siempre: entregar otra vez la respuesta solo puede ser rechazado. Por eso cada entrega lee primero la ejecución. Una ejecución que sigue siendo esta y está `Failed` ya contiene su respuesta; lo que necesita es una reanudación sin entrada con barrera sobre el intento en el que está *ahora*, que reutiliza los pasos confirmados y vuelve a ejecutar el fallido. Sin esa rama, un reembolso aprobado cuyo paso de pago falló una vez no se paga nunca. Con ella, ese paso puede ejecutarse dos veces, así que la llamada de pago que contiene debe llevar una clave de idempotencia construida con el ID del flujo de trabajo y el ID de ejecución, nunca con el intento, que cambia con cada reintento.

Los reintentos exigen que tres relojes estén de acuerdo, los mismos tres que en cualquier ejecución en cola (Capítulo 21). La concesión (`setLeaseTimeout(600)`) debe durar más que el paso individual más largo de la ejecución. El `$timeout` del trabajo debe durar más que la continuación más larga. Y el `retry_after` de la conexión de cola debe superar `$timeout`: `DB_QUEUE_RETRY_AFTER=360` para un `$timeout` de 300, donde Laravel trae 90 y entrega a un segundo proceso un trabajo que sigue ejecutándose. El trabajo de inicio de la Sección 22.2 declara los mismos `$tries` y `$timeout`.

::: {.callout .callout-warning}
[Dos barreras, dos tipos de excepción]{.callout-title}

En neuron-ai 4.0.2 solo la barrera del ID de ejecución lanza `StaleWorkflowRunException`. Un *intento* obsoleto (la misma ejecución, ya continuada por otro proceso) lanza un `WorkflowException` corriente cuyo mensaje empieza por *"Stale continuation"* (Apéndice A, punto 74), así que el `catch` de arriba lo deja pasar y el trabajo falla. Déjalo así. Un ID de ejecución obsoleto demuestra que la ejecución ya no existe o ha sido sustituida; un intento obsoleto solo dice que ha avanzado, y puede haber avanzado hacia un proceso que ha muerto después. El reintento vuelve a leer la ejecución: si ya no existe, el `catch` registra una operación nula; si falló, `request()` la termina; si sigue retenida, tras la tercera entrega el gancho `failed()` del trabajo (Sección 22.4) pone la aprobación delante de una persona. Si capturas esa excepción como operación nula, un reembolso aprobado que nadie está pagando se registra como inofensivo. Revisa el motor de tu versión instalada antes de confiar en cualquiera de los dos comportamientos.
:::

Entrega la respuesta con `ExecutionRequest::signal()` en lugar de `ExecutionRequest::resume()`. Ambos aceptan las dos barreras; el `signal()` de la Sección 15.3 comprueba además el nombre del evento, de modo que una decisión solo puede llegar a una ejecución que esté esperando `refund.decided`. Reserva el `resume()` sin entrada para los dos casos en que no hay nada que entregar: un plazo que comprobar y una ejecución fallida que terminar.

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

El humano edita el contenido; la versión editada vuelve al flujo de trabajo como la clave `content` de la carga. Añade `'content' => ['nullable', 'string']` a las reglas de validación y viaja sin cambios por el mismo trabajo. El patrón de colaboración de la Sección 15.3, en un formulario. Es mucho más útil que aprobar/rechazar para cualquier cosa que la IA haya redactado, porque la respuesta común es «casi».

### Puntos clave

- El motor impide la doble reanudación; `lockForUpdate()` mantiene honestos tus registros.
- Comprueba el estado mientras tienes el bloqueo; registra la decisión, envía la reanudación: nunca reanudes en línea.
- Reconstruye a partir de la clave de negocio, entrega la respuesta con `ExecutionRequest::signal()` y protege con barrera usando el ID de ejecución y el intento que guardaste.
- Reintenta el trabajo y lee la ejecución en cada entrega: una ejecución que falló después de que entrara la respuesta se termina con una reanudación sin entrada sobre su intento actual.
- Un ID de ejecución obsoleto es una operación nula: la ejecución ya no existe. Un intento obsoleto no prueba nada: deja que el trabajo falle y vuelva a intentarlo.
- Para contenido redactado, un área de texto gana a dos botones.

## 22.4 Tiempos de espera, zombis y despliegues

### Hacer caducar las aprobaciones estancadas

El plazo pertenece al flujo de trabajo. `RefundApprovalRequest` lleva `expiresAt`, y cuando llega después un `run(ExecutionRequest::resume())` sin entrada, el flujo de trabajo vuelve a entrar en el nodo que espera sin respuesta; `interruptIf()` devuelve `null` y el nodo toma su rama de tiempo agotado. El nodo nunca compara relojes, y en el núcleo no se ejecuta ningún temporizador: tu planificador solo tiene que llamar a la puerta:

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
                    ResumeRefundWorkflow::dispatch($approval, null);
                }
            });

        return self::SUCCESS;
    }
}
```

**No entregues nada; no fabriques un rechazo.** Una decisión `null` es una reanudación sin entrada. Antes del plazo (desfase de relojes entre servidores, una petición cuyo plazo se movió) el flujo de trabajo simplemente sigue suspendido y el trabajo vuelve. Después, el nodo registra una caducidad y la ejecución se completa, notifica y limpia. El `recordOutcome()` del trabajo marca la aprobación como `expired` a partir del estado que devolvió el flujo de trabajo, de modo que el registro sigue al flujo de trabajo y no al revés.

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

### Qué queda en el almacén

Una ejecución que se completa limpia tras de sí: un final limpio borra de forma condicional toda la partición de la ejecución en `workflow_store`, así que los reembolsos completados no dejan nada atrás. Lo que se acumula son las ejecuciones que nunca terminan: peticiones suspendidas que nadie responderá nunca, ejecuciones cuyo proceso falló y nadie reintentó.

No borres sus filas a mano. Las escrituras del almacén están protegidas por su registro de control, y un `DELETE` en bruto puede competir con un proceso que esté recuperando la misma ejecución. Pídeselo en cambio al motor:

```php
$engine = app(WorkflowEngine::class);

PendingApproval::query()
    ->where('status', 'failed')
    ->where('updated_at', '<', now()->subDays(30))
    ->each(function (PendingApproval $approval) use ($engine) {
        try {
            $engine->abandon($approval->workflow_id, $approval->run_id);
        } catch (StaleWorkflowRunException) {
            // Nothing of that run is left: it is gone, or a newer run holds the order.
        } catch (WorkflowException $e) {
            // Live under a lease, or a retained completion: not this sweep's to remove.
            report($e);
        }
    });
```

`WorkflowEngine` gestiona las ejecuciones por ID del flujo de trabajo sin construir el flujo de trabajo (todo lo que necesita un barrido), y Laravel lo inyecta automáticamente a partir de la vinculación de persistencia del Capítulo 18. Su `abandon()` descarta una ejecución en pausa, fallida o muerta y libera el ID del flujo de trabajo, protegido por la barrera del ID de ejecución que le pases. Omite el intento: el de tu tabla es el intento que se pausó, y una ejecución que falló después ya lo ha superado. Cuando `abandon()` no puede hacer lo que le pediste, lanza una excepción, y una excepción que escapa de `each()` termina el barrido; de ahí los dos `catch`. `StaleWorkflowRunException` significa que esa ejecución ya no tiene el ID: ya no existe, o el pedido tiene una ejecución más reciente. Un `WorkflowException` corriente es una negativa: una ejecución viva bajo una concesión, o una finalización retenida. Treinta días de gracia y luego se elimina.

### Procesos caídos y concesiones

Un proceso matado a mitad de una ejecución (el OOM killer, el `SIGKILL` de un despliegue, el tiempo de espera de un trabajo) no tiene ocasión de registrar nada. Su ejecución sigue marcada como `running`, y el motor no puede distinguirla de un proceso que simplemente va lento.

Una **concesión** lo resuelve. Con `setLeaseTimeout(600)` la ejecución mantiene un plazo que cada paso confirmado renueva; una vez vencido, la ejecución cuenta como muerta. Una reentrega del trabajo que la inició la recupera entonces, reutilizando los pasos confirmados (para eso sirve `recoverFailed: true` en el inicio reservado), y también lo hace un `run(ExecutionRequest::resume())` sin entrada; un `run()` sencillo la sustituiría y empezaría de nuevo. Sin concesión, solo un `run(ExecutionRequest::resume())` explícito puede hacerse cargo de la ejecución. Un agente mantiene por defecto una concesión de diez minutos; un flujo de trabajo simple no mantiene ninguna, y por eso ambos trabajos fijan una.

Elige la concesión por encima del tramo silencioso más largo entre dos pasos (una llamada lenta al proveedor, una petición de pago) y no por el `$timeout` del trabajo: cada uno de los tres relojes de la Sección 22.3 se mide contra algo distinto. Una concesión más corta que una llamada lenta al proveedor revive una ejecución que no estaba muerta, y entonces hay dos procesos ejecutándola.

### Finalizaciones perdidas

Queda un hueco. El `run()` del trabajo de reanudación completa el reembolso, y el proceso muere antes de que `recordOutcome()` escriba la fila de auditoría. El flujo de trabajo ha terminado y sus registros han desaparecido; tu tabla sigue diciendo `approved`, sin ningún reembolso registrado.

Para los flujos de trabajo en los que eso importa, conserva el resultado hasta que lo hayas registrado:

```php
$workflow = RefundWorkflow::make(orderId: $this->approval->subject_id)
    ->setPersistence($runs)
    ->setLeaseTimeout(600)
    ->retainCompletionUntilAcknowledged();

$state = $workflow->run($this->request($workflow->inspect()));

// ...the stale and still-waiting returns, as above

$this->recordOutcome($state);

$workflow->acknowledge($this->approval->run_id);
```

Con la retención activada, la finalización escribe el estado terminal en el almacén en lugar de borrarlo todo. Si el proceso muere antes de confirmar, la reentrega encuentra la ejecución `Completed`, y la respuesta que lleva es obsoleta. Lo que tiene que pedir es el resultado: `run(ExecutionRequest::resume(expectedRunId: $runId))`, sin carga, reproduce el resultado retenido sin ejecutar ningún nodo; tú lo registras y luego confirmas. En `request()` eso es un estado más en la primera rama: `Completed` junto a `Failed`. Hasta entonces el ID del flujo de trabajo sigue ocupado (un nuevo inicio para ese pedido lanza `RunInFlightException`, cuyo mensaje menciona `acknowledge()` y el ID de ejecución), que es exactamente el recordatorio que quieres.

### El problema de los despliegues, y cómo convivir con él

La Sección 15.4 lo señalaba; aquí va la gestión práctica.

La ejecución persistida contiene **tus clases**, serializadas: el estado, los eventos, la petición de interrupción pendiente. Renombra un nodo, cambia una clase de estado, añade una property tipada a una petición de interrupción, y la deserialización de las ejecuciones en vuelo se rompe.

Cuatro mitigaciones, en orden de utilidad:

**1. Mantén las peticiones de interrupción pequeñas y planas.** Cadenas, números, arrays. Sin modelos, sin conexiones, sin funciones anónimas. Cuanto menor sea la superficie, menos hay que romper.

**2. Añade propiedades con valores por defecto, y versiona la forma que viaja.**

```php
class RefundApprovalRequest extends WaitForEventRequest
{
    public const EVENT = 'refund.decided';

    public const VERSION = 2;

    // Added in version 2. Declared with a default, so requests suspended
    // by version 1 unserialise with 'EUR' instead of an uninitialised property.
    protected string $currency = 'EUR';

    public function __construct(
        final protected string $message,
        final protected int $orderId,
        final protected float $amount,
        ?DateTimeImmutable $expiresAt = null,
    ) {
        parent::__construct(self::EVENT, $expiresAt);
    }

    /**
     * The version-2 field is set with a wither, in the style of the
     * framework's own withId(): the constructor - and every call site written
     * for version 1 - stays as it was.
     *
     * PHP 8.5: clone() takes the properties to change, and #[\NoDiscard]
     * warns if the caller drops the copy and keeps the unchanged original.
     */
    #[\NoDiscard('withCurrency() returns a copy; the original request is unchanged.')]
    public function withCurrency(string $currency): static
    {
        return clone($this, ['currency' => $currency]);
    }

    public function getMessage(): string
    {
        return $this->message;
    }

    /**
     * @return array<string, mixed>
     */
    protected function metadata(): array
    {
        return [
            'version'  => self::VERSION,
            'message'  => $this->message,
            'orderId'  => $this->orderId,
            'amount'   => $this->amount,
            'currency' => $this->currency,
        ];
    }
}
```

Las dos mitades resuelven problemas distintos. La deserialización no ejecuta tu constructor, así que una propiedad que la versión 1 nunca escribió simplemente falta: si está declarada con un valor por defecto, la petición antigua vuelve con ese valor; si está promovida, o tipada sin valor por defecto, la primera lectura es un error fatal. La `version` de `metadata()` es para los demás lectores (la pantalla de aprobación y quien construya la carga de reanudación), de modo que un formulario renderizado a partir de una petición de la versión 1 todavía pueda responderse con la forma que espera el nodo.

Dos novedades de PHP 8.5 mantienen honesta la clase. Las propiedades promovidas son `final`, así que una subclase no puede redeclarar los campos que `metadata()` pone en la carga serializada; y `clone($this, ['currency' => $currency])` copia el objeto y fija las propiedades indicadas en una sola expresión, que es como `withCurrency()` añade el campo de la versión 2 sin tocar el constructor ni ningún punto de llamada escrito para la versión 1.

**3. Vacía antes de los despliegues arriesgados.** Para una versión que cambie clases de flujo de trabajo, deja de enviar flujos de trabajo nuevos, deja que se resuelvan los pendientes y luego despliega. Actualizar el propio NeuronAI cuenta como uno de ellos: las ejecuciones suspendidas con un formato de almacén más antiguo no se pueden reanudar con uno más nuevo.

**4. Falla ruidosamente.** Un trabajo de reanudación que no puede deserializar la ejecución lanza una excepción. Déjalo: marca la aprobación como `failed` desde el hook `failed()` del trabajo, registra el ID del flujo de trabajo y el ID de ejecución, y deja la ejecución para que una persona la recupere o la abandone. Un fallo visible es recuperable; uno silencioso no.

### Monitorización

Cuatro números que merecen un panel:

- Aprobaciones pendientes, por antigüedad
- Aprobaciones caducadas en los últimos 7 días: un número creciente significa que lo que está roto es tu proceso, no tu código
- Reanudaciones fallidas, y reanudaciones obsoletas ignoradas: un goteo constante de las segundas es normal; un pico significa que algo está reentregando
- Aprobaciones atascadas en `approved` sin resultado registrado: las finalizaciones perdidas de la sección anterior

### Puntos clave

- Haz caducar con una reanudación sin entrada; el flujo de trabajo comprueba su propio plazo y toma su rama de tiempo agotado.
- Escala antes de hacer caducar.
- Las ejecuciones completadas se borran solas; limpia el resto con `abandon()`, nunca con un `DELETE` en bruto, y espera que lance una excepción cuando no haya nada que abandonar.
- Fija una concesión superior al paso silencioso más largo, un `$timeout` superior al trabajo más largo y un `retry_after` superior a `$timeout`; retén las finalizaciones que no te puedes permitir perder.
- El estado serializado contiene tus clases: mantén las peticiones planas, da valores por defecto a las propiedades nuevas, vacía antes de los despliegues arriesgados y falla ruidosamente.

## 22.5 Aprobación de herramientas de un agente en Laravel

El flujo de trabajo de reembolsos es dueño de su pausa: es un nodo el que decide interrumpir. La pausa de un agente, en cambio, viene de una herramienta. La Sección 15.5 mostró el mecanismo: la herramienta declara una política de aprobación, el `ToolNode` del agente interrumpe con una acción por cada llamada sujeta a aprobación y `submitApprovalDecisions()` continúa la ejecución. Esto es lo que hace falta en una aplicación Laravel.

### El agente

```php
class SupportAgent extends Agent
{
    public function __construct(
        protected MessageStoreInterface $conversations,
        protected PersistenceInterface $runs,
    ) {
        parent::__construct();
    }

    protected function messageStore(): MessageStoreInterface
    {
        return $this->conversations;   // durable: it holds the pending tool call
    }

    protected function persistence(): PersistenceInterface
    {
        return $this->runs;            // durable: it holds the paused run
    }

    protected function tools(): array
    {
        $scope = ThreadScope::of($this->getThreadId());

        return [
            new SearchOrdersTool($scope->tenantId),
            (new IssueRefundTool($scope->tenantId))->requireApproval(),
        ];
    }

    // provider(), contextWindow() and recoverFailedTurn() as in Chapter 18
}
```

Dos colaboradores duraderos, y ambos son obligatorios. La **persistencia del flujo de trabajo** guarda la ejecución en pausa; el almacén en memoria por defecto la olvidaría al terminar la petición. Un **almacén de mensajes duradero** guarda la conversación, incluida la llamada a herramienta pendiente del asistente; sin él, el hilo no puede continuar en otra petición. Son las dos vinculaciones del Capítulo 18, inyectadas por el contenedor y devueltas desde los dos ganchos, y tienen que ser precisamente esos ganchos. Un agente que sigue sobrescribiendo `chatHistory()` carga y se pausa sin error mientras su conversación se queda en memoria (Sección 18.2). La tarjeta de aprobación se sigue mostrando, porque la ejecución en pausa es duradera; aprobarla falla con `ChatHistoryException`, porque la llamada a herramienta a la que responde ya no está en ningún historial.

A ninguno de los dos se le da el ID de hilo. Los almacenes son servicios compartidos; el hilo se vincula en cada petición, con `for()`. Más aún: **el ID de hilo es el ID del flujo de trabajo del agente.** La ejecución en pausa se archiva en `workflow_store` bajo el hilo, así que todo lo que necesite encontrarla (el punto de conexión de aprobación, la página que se recarga) necesita el hilo y nada más. No hay ningún ID de ejecución que guardar, y por eso aquí encaminar una decisión no necesita una tabla `pending_approvals`. El registro de quién aprobó qué sigue siendo cosa tuya: escríbelo en `decide()`.

### Un punto de conexión para el turno, otro para las decisiones

```php
class ThreadController extends Controller
{
    public function chat(
        Request $request,
        Conversation $conversation,
        SupportAgent $agent,
    ): JsonResponse {
        Gate::authorize('participate', $conversation);

        $validated = $request->validate(['message' => ['required', 'string', 'max:4000']]);

        $agent = $agent->for($conversation->threadId());
        $agent->recoverFailedTurn();

        try {
            $state = $agent->chat(new UserMessage($validated['message']));
        } catch (RunInFlightException $e) {
            // suspended: decisions are pending; running: another request holds the turn
            return response()->json([
                'status'  => $e->status->value,
                'pending' => $agent->pendingApprovals(),
            ], 409);
        }

        return $this->respond($agent, $state);
    }

    public function pending(Conversation $conversation, SupportAgent $agent): JsonResponse
    {
        Gate::authorize('participate', $conversation);

        return response()->json(
            $agent->for($conversation->threadId())->pendingApprovals()
        );
    }

    public function decide(
        Request $request,
        Conversation $conversation,
        SupportAgent $agent,
    ): JsonResponse {
        Gate::authorize('approveTools', $conversation);

        $validated = $request->validate(['decisions' => ['required', 'array']]);

        $agent = $agent->for($conversation->threadId());

        try {
            $state = $agent->submitApprovalDecisions($validated['decisions'])->run();
        } catch (InputTranslationException $e) {
            return response()->json(['error' => $e->getMessage()], 400);
        } catch (WorkflowException $e) {
            // Two approvers at once, and the other one won: send back what is still open.
            return response()->json([
                'status'  => 'conflict',
                'pending' => $agent->pendingApprovals(),
            ], 409);
        }

        return $this->respond($agent, $state);
    }

    private function respond(SupportAgent $agent, AgentState $state): JsonResponse
    {
        return response()->json($state->isInterrupted()
            ? ['status' => 'awaiting_approval', 'pending' => $agent->pendingApprovals()]
            : ['status' => 'completed', 'answer' => $state->getMessage()?->getContent()]);
    }
}
```

### Qué hace cada pieza

**`RunInFlightException` es el bloqueo que olvidaste construir.** Un mensaje nuevo en un hilo cuya ejecución espera una decisión lo rechaza el motor antes de que nada llegue al modelo o al almacén. Tradúcelo a HTTP 409 y devuelve las acciones pendientes, para que el cliente pueda volver a mostrarlas. Tu interfaz debería bloquear la entrada mientras haya aprobaciones abiertas; esto es lo que pasa cuando no lo hace. La misma excepción con el estado `running` es una segunda petición que llega mientras un turno sigue ejecutándose: el mismo 409, sin nada pendiente.

**`recoverFailedTurn()` va antes que `chat()`.** La quinta pregunta de la Sección 18.4 pesa aquí más que en ningún otro sitio. Quien aprueba dice que sí, el reembolso se emite y el proveedor falla en la llamada siguiente: la ejecución queda `failed` con su pregunta ya almacenada, y todo mensaje posterior en ese hilo se rechaza con `ChatHistoryException`. Terminar primero el turno fallido reutiliza los pasos confirmados (el reembolso no se emite por segunda vez) y cuesta una lectura cuando no hay nada que terminar.

**`pendingApprovals()` sobrevive a una recarga de la página.** Lee la interrupción persistida en un proceso en frío y devuelve los objetos `Action` que siguen esperando una decisión, cada uno con el ID de la llamada a herramienta como `id`, el nombre de la herramienta, el motivo que dio la herramienta para pedirla y sus `inputs`. Es lo que la página llama al montarse. También refleja el progreso parcial: una acción ya decidida deja de devolverse.

**Las decisiones se indexan por ID de llamada a herramienta** y adoptan tres formas: `'approve'`, `'reject'` o `['reject', 'reason']`. Los envíos son incrementales: una petición puede llevar solo las acciones recién decididas, y la ejecución vuelve a suspenderse hasta que estén todas. Una herramienta solo se ejecuta si se aprueba explícitamente; el silencio nunca es consentimiento. Una decisión para un ID de llamada que la ejecución no está esperando se rechaza con `InputTranslationException` antes de ejecutar nada: un 400, no un 500.

**Dos aprobadores pueden chocar igualmente.** Ambos abren la misma tarjeta y ambos envían. `submitApprovalDecisions()` captura la ejecución y el intento que leyó, así que solo se acepta una continuación; el `run()` del otro lanza un `WorkflowException` (`StaleWorkflowRunException` cuando el ganador ya ha terminado la ejecución, uno corriente mientras el ganador sigue ejecutándose). Es un 409 con lo que siga pendiente, y una página que se recarga, no un 500. Los estados son los de la correspondencia a nivel de aplicación en `bootstrap/app.php` (Capítulo 21); los `catch` locales están para enviar con ellos las acciones pendientes.

**Quien aprueba no tiene por qué ser quien chatea.** `decide()` autoriza una habilidad distinta de `chat()`. La petición de reembolso de un cliente puede esperar en su conversación mientras un responsable, en otra pantalla, llama a `pendingApprovals()` para ese hilo y envía la decisión. El ID de hilo es el único asidero que necesitan ambos, y por eso debe venir de un registro para el que el usuario esté autorizado, nunca directamente de la petición (Sección 18.2).

### Caducidad de las aprobaciones de agentes

Una aprobación de herramienta no lleva plazo propio: una ejecución de agente suspendida no mantiene ninguna concesión y espera indefinidamente. Si tu producto necesita un plazo, guárdalo en tu aplicación y cancela rechazando:

```php
$agent = app(SupportAgent::class)->for($conversation->threadId());

$agent->submitApprovalDecisions(
    collect($agent->pendingApprovals())
        ->mapWithKeys(fn (Action $action) => [$action->id => ['reject', 'No decision within 48 hours']])
        ->all()
)->run();
```

El modelo recibe el rechazo como resultado de la herramienta y responde al cliente en consecuencia, y el hilo vuelve a quedar libre. No recurras aquí a `abandon()`: en un agente lanza una `AgentException` mientras haya una aprobación pendiente, porque dejaría una llamada a herramienta sin respuesta en la conversación. `resetConversation()` sí libera el hilo, al precio de borrar su historial.

### Puntos clave

- Un agente con aprobaciones necesita persistencia del flujo de trabajo duradera y un almacén de mensajes duradero, devueltos desde `persistence()` y `messageStore()`.
- El ID de hilo es el ID del flujo de trabajo: un único asidero para el turno, las decisiones y la recarga.
- `RunInFlightException` significa «decisiones pendientes»: devuelve 409 con `pendingApprovals()`; una carrera perdida entre dos aprobadores también es un 409.
- Recupera un turno fallido antes de cada `chat()`.
- `pendingApprovals()` reconstruye la interfaz de aprobación tras una recarga; las decisiones son incrementales y se indexan por ID de llamada a herramienta.
- Las aprobaciones de agentes no tienen plazo; hazlas caducar enviando rechazos.

## Laboratorio 16 — Aprobación de reembolsos, de principio a fin

**Cubre:** toda la Parte IV y toda la Parte V. Este es el laboratorio que demuestra que el patrón es desplegable.

### Objetivo

Un agente prepara un reembolso. El flujo de trabajo se detiene. Un responsable aprueba desde una pantalla autenticada. El flujo de trabajo se reanuda en un proceso y ejecuta el reembolso, sobreviviendo entretanto a un reinicio de proceso y a un despliegue.

### El flujo

```
El cliente pide un reembolso
   ↓
El agente reúne el pedido, comprueba la elegibilidad, prepara el caso   (memoizado)
   ↓
¿Reembolso por encima de 100 €?  → interrupción, con un expiresAt de 48 horas
   ↓
Fila PendingApproval (ID del flujo de trabajo, ID de ejecución, intento) + notificación a quienes aprueban
   ↓                                      (pasan las horas; nada se está ejecutando)
El responsable abre la pantalla de aprobación, ve el pedido y el caso
   ↓
Aprueba (con un importe ajustado opcional) o rechaza con realimentación
   ↓
Trabajo ResumeRefundWorkflow, con barrera → reembolso ejecutado → fila de auditoría → cliente notificado
```

### Requisitos

1. **Memoiza todo antes de la interrupción.** Sección 15.5. El caso que lee el responsable debe ser el caso sobre el que actúa el flujo de trabajo.
2. **`interruptIf()`** para que los reembolsos por debajo de 100 € nunca interrumpan.
3. **Un registro `pending_approvals`** con relación polimórfica al `Order`, que guarde el ID de ejecución, el ID de interrupción y el intento de ejecución, para que la pantalla muestre sobre qué se está decidiendo y la reanudación pueda protegerse con barrera.
4. **`lockForUpdate()`** al resolver, con el estado comprobado dentro del bloqueo.
5. **Reanudación enviada, no en línea**, con `expectedRunId` y `expectedExecutionAttempt`, en un trabajo que puede reintentarse.
6. **`expiresAt` a 48 horas** en la petición, escalado a 24, ambos impulsados por el planificador.
7. **Una fila de auditoría** para el reembolso, que nombre a quien aprobó.

### Criterios de aceptación

- Un reembolso de 40 € se completa sin intervención humana.
- Un reembolso de 400 € crea una aprobación, notifica, y nada se ejecuta hasta que se resuelve.
- Una segunda petición de reembolso para el mismo pedido mientras la primera está pendiente se rechaza con un mensaje claro, no con un trabajo fallido.
- Dos pestañas del navegador pinchando ambas aprobar producen **un** reembolso y un mensaje de «ya resuelta» en la segunda.
- Reiniciar el proceso de cola y el servidor de aplicación entre la interrupción y la reanudación no cambia nada.
- Un reembolso aprobado cuyo paso de pago lanza una excepción una vez se paga con el reintento del trabajo (una sola vez, con el caso preparado una sola vez) en lugar de quedarse aprobado y sin pagar.
- El importe de la fila de auditoría coincide con el importe que vio quien aprobó. Demuéstralo registrando dentro de la función anónima memoizada y confirmando que se ejecutó una sola vez.
- Una aprobación dejada 48 horas caduca, se reanuda sin respuesta, toma la rama de tiempo agotado del nodo y notifica al cliente, en lugar de quedarse pendiente para siempre.

### Los dos modos de fallo que reproducir deliberadamente

**Doble reanudación.** Quita el bloqueo, pincha aprobar en dos pestañas y observa qué pasa. El motor sigue pagando una sola vez (el segundo trabajo de reanudación se rechaza por obsoleto y no paga nada), pero ahora tu tabla registra dos aprobadores para un solo reembolso. Vuelve a poner el bloqueo. Después quita las barreras del trabajo, envíalo dos veces a mano y lee el fallo del segundo trabajo: ese es el error que habrían visto tus usuarios.

**Regeneración sin memoizar.** Mueve la preparación del caso dentro del propio nodo de aprobación, sin `memoize()`, y confirma que la ejecución reanudada produce un caso distinto del aprobado. Un nodo reanudado se vuelve a ejecutar desde el principio. En un flujo de trabajo de reembolsos eso no es una ineficiencia: es aprobar un importe y pagar otro. Después devuélvela a su propio nodo, o envuélvela en `memoize()`, y observa cómo la línea registrada aparece exactamente una vez.

Ambos son experimentos de cinco minutos, y ambos convencen más que cualquier cantidad de prosa sobre por qué existen esas salvaguardas.

### Ir más allá

Añade una simulación de despliegue: interrumpe un flujo de trabajo, añade una property tipada *sin valor por defecto* a tu clase de petición de interrupción, despliega e intenta la reanudación. Míralo fallar en la primera lectura de esa propiedad. Después declara la propiedad con un valor por defecto, como en la Sección 22.4, y mira cómo la misma ejecución suspendida se reanuda. Ese es el ejercicio que convierte «mantén planas las peticiones de interrupción» de consejo en una regla que seguirás de verdad.
