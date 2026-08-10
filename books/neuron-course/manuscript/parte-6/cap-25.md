# Chapter 25 — Capstone B: The Agentic Support Desk

**Stack:** Laravel 12 + `neuron-core/neuron-laravel`.
**Covers:** everything in this book.

## What you are building

A multi-tenant customer support application where an agent handles enquiries end to end:

- Answers policy questions from a knowledge base (RAG)
- Looks up orders and shipment status (tools)
- Prepares refunds, which pause for human approval above a threshold (workflow + interruption)
- Streams its work to the customer live
- Escalates to a human when it cannot help
- Records everything for audit

This is Case C from Section 1.7 — the one where all four questions pointed to rung 4. It earns every piece of machinery in this book, which is exactly why it is the capstone.

## The architecture

```
Customer (Livewire chat)
   │
   ├─ POST message
   │
SupportAgent (RAG + tools + Eloquent history)
   │
   ├─ policy question → retrieval, tenant + visibility filtered
   ├─ order question  → SearchOrdersTool / GetOrderStatusTool
   └─ refund request  → RefundWorkflow
                          │
                          ├─ EligibilityNode   (structured output)
                          ├─ AmountNode        (tool: compute refund)
                          ├─ ApprovalNode      (interrupt if > threshold)
                          │      │
                          │      └─ EloquentPersistence → PendingApproval row
                          │                                    │
                          │                              Manager approves
                          │                                    │
                          │                              ResumeWorkflow job
                          │
                          └─ ExecuteRefundNode (idempotent, audited)
```

## Build order

**1 — Laravel setup.** `composer require`, publish config and migrations, a `Neuron` facade smoke test, the `app/Neuron` structure.

**2 — Domain scaffolding.** Tenants, users, orders, refunds, knowledge base articles. Factories and seeders. No AI yet — deliberately, so you see how little of the application is agentic.

**3 — The first agent.** `SupportAgent` with dependency injection, `EloquentChatHistory` scoped by tenant and user, a controller, a plain Blade page.

**4 — Knowledge base ingestion.** The `IndexArticle` job, a custom Markdown splitter, metadata for tenant and visibility, the `indexed_at` gap alert.

**5 — RAG with permission filters.** `vectorStore()` with tenant and visibility filters, the anti-hallucination system prompt, and the CI test asserting a restricted article never surfaces.

**6 — Order tools.** `SearchOrdersTool` and `GetOrderStatusTool` with the tenant as a constructor dependency, column selection, bounded results, empty-case strings.

**7 — Streaming chat with Livewire.** `wire:stream`, tool-activity labels through an allowlist, the buffering checklist verified against staging.

**8 — The refund workflow.** Events, nodes, `RefundEligibility` structured output, the bounded loop, a `WorkflowState` subclass.

**9 — Human in the loop.** `interrupt()` with a custom `RefundApprovalInterrupt`, `checkpoint()` around the eligibility call, `EloquentPersistence`, the `PendingApproval` table.

**10 — The approval screen.** Index and detail pages, a policy, `lockForUpdate()` resolution, the `ResumeWorkflow` job, notifications with expiry.

**11 — Observability and evals.** Inspector with the Laravel package, usage logging, an eval suite with `FaithfulnessJudge`, the tenant-isolation and permission tests in CI.

**12 — Production hardening.** Budgets, rate limits, provider fallback, the audit table, and the deployment checklist from Section 23.6 worked through item by item.

## The three hardest parts

### 1. The checkpoint bug

Build it wrong first. Compute refund eligibility inside `ApprovalNode` without a checkpoint, interrupt, resume — and observe that the recomputed eligibility differs from what the manager approved.

Then wrap it:

```php
$eligibility = $this->checkpoint('eligibility', fn () => EligibilityAgent::make()->structured(
    new UserMessage($this->describeOrder($order)),
    RefundEligibility::class
));
```

Same content on resume.

**This is the single most valuable twenty minutes in the capstone** — a demonstrable correctness failure, fixed in one line, that no tutorial covers. In a refund workflow it is the difference between approving one amount and paying another.

### 2. Idempotent refund execution

```php
class ExecuteRefundNode extends Node
{
    public function __invoke(RefundApproved $event, RefundState $state): StopEvent
    {
        $refund = DB::transaction(function () use ($event, $state) {
            $order = Order::whereKey($state->orderId())->lockForUpdate()->firstOrFail();

            $existing = $order->refunds()
                ->where('workflow_id', $state->workflowId())
                ->first();

            if ($existing !== null) {
                return $existing;   // this workflow already refunded — return the same record
            }

            return $order->refunds()->create([
                'amount'      => $event->amount,
                'reason'      => $event->reason,
                'workflow_id' => $state->workflowId(),
                'approved_by' => $event->approvedBy,
            ]);
        });

        AgentAction::record($state, 'execute_refund', ['refund_id' => $refund->id]);

        return new StopEvent(result: $refund->id);
    }
}
```

The `workflow_id` on the refund record is the idempotency key. A workflow resumed twice — because a job retried, or two managers approved simultaneously — creates one refund.

This is not an AI concern. It is ordinary distributed-systems hygiene, and it matters here because agentic systems retry and resume far more than typical request handlers.

### 3. The escalation path

Every agent needs a way to give up:

```php
class EscalateTool extends Tool
{
    public function __construct(
        private readonly Conversation $conversation,
    ) {
        parent::__construct(
            'escalate_to_human',
            'Hand this conversation to a human support agent. Use this when you cannot answer '
            . 'from the knowledge base, when the customer explicitly asks for a human, when the '
            . 'customer is upset, or when the request is outside what your tools can do. '
            . 'Using this tool is always an acceptable outcome — prefer it over guessing.'
        );
    }

    public function __invoke(string $reason): string
    {
        $this->conversation->escalate($reason);

        return 'This conversation has been passed to a human agent. '
             . 'Tell the customer someone will reply shortly.';
    }
}
```

> **"Using this tool is always an acceptable outcome — prefer it over guessing."**

That sentence is the most important string in the application. Without an explicit escape hatch, a model faced with an impossible request will invent something, because producing an answer is what it does. Giving it a legitimate way to fail is the most effective anti-hallucination measure in the entire system, and it costs one tool.

## Assessment rubric

| Area | Criterion |
|---|---|
| **Isolation** | Tenant test passes with colliding conversation IDs |
| **Retrieval** | Restricted-article test passes; filters applied inside `vectorStore()` |
| **Tools** | Constructor-scoped; bounded; `visible()` from policies; write tools capped at 1 |
| **Workflow** | Every pre-interrupt LLM call checkpointed; loops bounded |
| **Approval** | `lockForUpdate()` resolution; expiry scheduled; resume dispatched not inline |
| **Idempotency** | Refund carries a workflow-scoped key; double resume creates one record |
| **Observability** | Inspector configured with `autoFlush` on workers; usage logged |
| **Quality** | Eval suite with `FaithfulnessJudge`; a recorded baseline score |
| **Audit** | Every consequential tool writes an `agent_actions` row |
| **Escalation** | The agent has, and uses, a way to give up |

## The final exercise

Answer the five questions from Section 23.6 about your own capstone, in writing:

1. What does this agent cost per request, and at what volume does that become a problem?
2. What is the worst thing it can do, and what stops it?
3. How would I find out what it did, three weeks from now?
4. What happens when the provider is down?
5. What data leaves my infrastructure, and where does it go?

Write the answers down rather than thinking them through. The ones that are hard to write are the ones where the system is not finished.

Someone who can answer all five about code they wrote themselves has finished this book in the way that matters.
