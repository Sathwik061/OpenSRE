import type { HistoryRecord, IncidentCase, InvestigatePayload } from "./types";

export const INCIDENT_CASES: IncidentCase[] = [
  {
    id: "form-not-found",
    label: "Missing Form Definition",
    category: "Camunda Workflow",
    service: "camunda-tasklist",
    environment: "production",
    severity: "high",
    errorType: "FORM_NOT_FOUND",
    errorMessage:
      "Expected to find form with id 'customer-onboarding-form' but no form with this id is deployed",
    elementId: "Activity_CollectCustomerData",
    processDefinitionId: "customer-onboarding-process",
    logs: [
      "2026-08-31T10:14:02.113Z WARN  [zeebe-gateway] Job activation failed for element Activity_CollectCustomerData",
      "2026-08-31T10:14:02.119Z ERROR [tasklist] FormNotFoundException: form 'customer-onboarding-form' not deployed in tenant <default>",
      "2026-08-31T10:14:02.402Z ERROR [zeebe-broker] Incident created key=2251799813685301 type=FORM_NOT_FOUND",
    ],
    timeline: [
      "10:12:40 — Deployment v14 of customer-onboarding-process published",
      "10:14:02 — First user task instance failed to render form",
      "10:15:10 — 38 process instances blocked at Activity_CollectCustomerData",
    ],
    variables: {
      customerId: "CUS-99231",
      channel: "web",
      onboardingTier: "premium",
      retryCount: "3",
    },
  },
  {
    id: "dmn-eval-failure",
    label: "DMN Evaluation Failure",
    category: "Decision Engine",
    service: "camunda-zeebe",
    environment: "production",
    severity: "critical",
    errorType: "DECISION_EVALUATION_ERROR",
    errorMessage:
      "Expected to evaluate decision 'risk-scoring', but failed to evaluate expression 'creditScore': no variable found for name 'creditScore'",
    elementId: "BusinessRuleTask_RiskScoring",
    processDefinitionId: "loan-approval-process",
    logs: [
      "2026-08-31T11:02:44.881Z ERROR [zeebe-broker] DecisionEvaluationException on decision risk-scoring",
      "2026-08-31T11:02:44.884Z DEBUG [zeebe-broker] variable scope: {applicantId, requestedAmount, tenure}",
      "2026-08-31T11:02:45.011Z ERROR [zeebe-broker] Incident created type=DECISION_EVALUATION_ERROR",
    ],
    timeline: [
      "10:58:00 — Upstream credit-bureau adapter began returning null scores",
      "11:02:44 — First DMN evaluation failure",
      "11:06:00 — 112 loan applications stalled",
    ],
    variables: {
      applicantId: "APP-7741",
      requestedAmount: "42000",
      tenure: "36",
      bureauResponse: "null",
    },
  },
  {
    id: "feel-condition-error",
    label: "FEEL Condition Error",
    category: "Camunda Workflow",
    service: "camunda-zeebe",
    environment: "staging",
    severity: "medium",
    errorType: "FEELExpressionEvaluationError",
    errorMessage:
      "failed to evaluate expression 'amount > threshold': no variable found for name 'threshold'",
    elementId: "Gateway_AmountCheck",
    processDefinitionId: "payment-routing-process",
    logs: [
      "2026-08-31T09:31:18.204Z ERROR [zeebe-broker] FEELExpressionEvaluationError at Gateway_AmountCheck",
      "2026-08-31T09:31:18.207Z INFO  [zeebe-broker] available variables: amount, currency, merchantId",
      "2026-08-31T09:31:18.512Z ERROR [zeebe-broker] Incident created type=CONDITION_ERROR",
    ],
    timeline: [
      "09:28:00 — payment-routing-process v7 deployed without threshold default",
      "09:31:18 — Gateway evaluation failed",
      "09:40:00 — 9 staging instances blocked",
    ],
    variables: { amount: "1250.00", currency: "EUR", merchantId: "MER-2213" },
  },
  {
    id: "db-pool-exhaustion",
    label: "Database Connection Pool Exhaustion",
    category: "Infrastructure",
    service: "orders-api",
    environment: "production",
    severity: "critical",
    errorType: "CONNECTION_POOL_EXHAUSTED",
    errorMessage:
      "HikariPool-1 - Connection is not available, request timed out after 30000ms (total=50, active=50, idle=0, waiting=87)",
    elementId: "ServiceTask_PersistOrder",
    processDefinitionId: "order-fulfillment-process",
    logs: [
      "2026-08-31T14:20:11.004Z WARN  [orders-api] HikariPool-1 - Thread starvation or clock leap detected",
      "2026-08-31T14:20:41.771Z ERROR [orders-api] SQLTransientConnectionException: request timed out after 30000ms",
      "2026-08-31T14:21:02.330Z ERROR [orders-api] 503 returned for POST /orders (p99 latency 31.4s)",
    ],
    timeline: [
      "14:05:00 — Nightly reconciliation job started holding long transactions",
      "14:20:11 — Pool saturation first observed",
      "14:22:00 — Order API error rate reached 64%",
    ],
    variables: { orderId: "ORD-556231", region: "eu-central-1", poolSize: "50", waiting: "87" },
  },
  {
    id: "kafka-producer-timeout",
    label: "Kafka Producer Timeout",
    category: "Messaging",
    service: "event-bridge",
    environment: "production",
    severity: "high",
    errorType: "KAFKA_TIMEOUT",
    errorMessage:
      "Expiring 148 record(s) for topic order-events-0: 120000 ms has passed since batch creation",
    elementId: "ServiceTask_PublishOrderEvent",
    processDefinitionId: "order-fulfillment-process",
    logs: [
      "2026-08-31T16:44:02.119Z WARN  [event-bridge] Connection to node 3 (broker-3:9092) could not be established",
      "2026-08-31T16:45:12.884Z ERROR [event-bridge] TimeoutException: Expiring 148 record(s) for order-events-0",
      "2026-08-31T16:45:13.002Z ERROR [event-bridge] producer buffer 96% full, backpressure engaged",
    ],
    timeline: [
      "16:41:00 — Broker-3 rolling restart initiated by platform team",
      "16:44:02 — Producer lost leader for partition 0",
      "16:45:12 — Record batches expired, downstream events dropped",
    ],
    variables: { topic: "order-events", partition: "0", pendingRecords: "148", acks: "all" },
  },
  {
    id: "http-500-service-down",
    label: "HTTP 500 Service Down",
    category: "Service Health",
    service: "payment-gateway",
    environment: "production",
    severity: "critical",
    errorType: "HTTP_500",
    errorMessage: "Upstream payment gateway returned 500 Internal Server Error for POST /charges",
    elementId: "ServiceTask_ChargeCard",
    processDefinitionId: "checkout-process",
    logs: [
      "2026-08-31T18:02:41.552Z ERROR [payment-gateway] 500 from provider api.pay-provider.io /v1/charges",
      "2026-08-31T18:02:41.559Z ERROR [checkout-worker] job failed, retries=0 remaining",
      "2026-08-31T18:03:00.100Z ERROR [zeebe-broker] Incident created type=JOB_NO_RETRIES",
    ],
    timeline: [
      "18:00:20 — Provider status page reported degraded performance",
      "18:02:41 — First 500 responses observed",
      "18:05:00 — 214 checkouts failed, revenue impact detected",
    ],
    variables: { checkoutId: "CHK-88213", amount: "89.90", currency: "USD", provider: "pay-provider" },
  },
];

export function caseToPayload(c: IncidentCase): InvestigatePayload {
  return {
    alert_name: c.label,
    service: c.service,
    environment: c.environment,
    error: c.errorType,
    error_message: c.errorMessage,
    logs: c.logs,
    timeline: c.timeline,
    severity: c.severity,
    request: `Investigate ${c.errorType} in ${c.service} (${c.environment})`,
  };
}

export function newId(prefix = "rec") {
  return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

export function caseToRecord(c: IncidentCase): HistoryRecord {
  return {
    id: newId("case"),
    savedAt: new Date().toISOString(),
    source: "template",
    title: c.label,
    service: c.service,
    environment: c.environment,
    severity: c.severity,
    errorType: c.errorType,
    errorMessage: c.errorMessage,
    resolutionStatus: "open",
    elementId: c.elementId,
    processDefinitionId: c.processDefinitionId,
    creationTime: new Date().toISOString(),
    variables: c.variables,
    payload: caseToPayload(c),
  };
}
