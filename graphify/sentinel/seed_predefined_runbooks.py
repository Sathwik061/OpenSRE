"""
seed_predefined_runbooks.py — Seed Predefined Open SRE Runbooks into Supabase
=============================================================================
Seeds comprehensive, production-grade SRE Runbooks with predefined instructions
tailored specifically for all Open SRE and Camunda failure scenarios.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "sentinel"))

from supabase_runbook import SUPABASE_URL, SUPABASE_KEY, is_configured, _post, _get, TABLE

PREDEFINED_RUNBOOKS = [
    {
        "error_type": "CONDITION_ERROR",
        "process_id": "*",
        "summary": "BPMN sequence flow evaluation failed because no condition matched the input variables and no default flow was defined.",
        "root_cause": "The BPMN exclusive (XOR) or inclusive gateway has outgoing sequence flows with condition expressions, but none evaluated to true given the current runtime process variables. Additionally, no default sequence flow was configured to catch unmatched cases.",
        "observed_facts": [
            "Error type is CONDITION_ERROR",
            "Gateway failed to evaluate outgoing sequence flow conditions to true",
            "Runtime variable state did not satisfy any sequence flow condition",
            "No default sequence flow is defined on the gateway"
        ],
        "recommended_actions": [
            "Open Camunda Modeler and inspect the outgoing sequence flow expressions on the failing gateway.",
            "Verify all condition expressions against the runtime process variables (e.g. carType, Experience, risk, amount, threshold).",
            "Add null-safe defensive FEEL expressions: if is defined(myVar) and myVar != null then (condition) else false.",
            "Always configure a Default Sequence Flow on the XOR gateway to prevent unhandled routing deadlock.",
            "Test the process with edge-case variable payloads in a local test environment.",
            "Deploy the updated BPMN model to Camunda Zeebe and resolve the incident in Camunda Operate."
        ],
        "confidence": "HIGH",
        "source": "predefined_sre_runbook",
        "use_count": 1
    },
    {
        "error_type": "FORM_NOT_FOUND",
        "process_id": "customer-onboarding-process",
        "summary": "User task failed because the referenced form definition is missing from the Camunda Form Registry.",
        "root_cause": "The BPMN user task references a form by formId/formKey ('customer-onboarding-form') that does not exist in the active Camunda Form registry. This occurs when the form JSON schema was not deployed alongside the BPMN process or was deleted.",
        "observed_facts": [
            "Error type is FORM_NOT_FOUND",
            "User task Activity_CollectCustomerData cannot render form 'customer-onboarding-form'",
            "Form definition is missing in tenant <default>",
            "Process instances are blocked at the user task stage"
        ],
        "recommended_actions": [
            "In Camunda Modeler, inspect the user task and verify the linked formId / formKey ('customer-onboarding-form').",
            "Check the Camunda Tasklist and Zeebe form registry to confirm if the form schema exists in the active tenant.",
            "Deploy the .form JSON schema file alongside the BPMN process using Camunda Web Modeler or the Desktop Modeler Deploy button.",
            "Ensure the form schema binding (schemaVersion) is compatible with Camunda 8.9 runtime.",
            "Once the form is deployed, retry the blocked user task instances in Camunda Operate."
        ],
        "confidence": "HIGH",
        "source": "predefined_sre_runbook",
        "use_count": 1
    },
    {
        "error_type": "DECISION_EVALUATION_ERROR",
        "process_id": "loan-approval-process",
        "summary": "DMN Decision Table evaluation failed due to a missing or null input variable (e.g. creditScore).",
        "root_cause": "The DMN decision table ('risk-scoring') attempted to evaluate an input clause expression ('creditScore'), but the variable was not present in the process instance scope or was returned as null by an upstream adapter.",
        "observed_facts": [
            "Error type is DECISION_EVALUATION_ERROR",
            "Decision 'risk-scoring' failed at BusinessRuleTask_RiskScoring",
            "Required variable 'creditScore' is null or missing in variable scope",
            "Upstream credit bureau integration returned null payload"
        ],
        "recommended_actions": [
            "Open the DMN model ('risk-scoring.dmn') and inspect all required input clause expressions.",
            "Check upstream worker tasks (e.g. credit bureau adapter) and ensure all mandatory variables are populated prior to DMN evaluation.",
            "Add defensive default fallback rules in the DMN decision table (e.g. Hit Policy UNIQUE or FIRST with default score when null).",
            "Implement input data validation in the upstream service worker to catch null API responses before triggering the DMN.",
            "Deploy the updated DMN decision definition to Zeebe and retry the incident in Camunda Operate."
        ],
        "confidence": "HIGH",
        "source": "predefined_sre_runbook",
        "use_count": 1
    },
    {
        "error_type": "CONNECTION_POOL_EXHAUSTED",
        "process_id": "order-fulfillment-process",
        "summary": "Database connection pool saturated (HikariCP timeout after 30000ms).",
        "root_cause": "The service task 'ServiceTask_PersistOrder' in 'orders-api' exhausted its HikariCP connection pool (total=50, active=50, waiting=87). Long-running batch transactions or unclosed database connections caused thread starvation and HTTP 503 service degradation.",
        "observed_facts": [
            "Error type is CONNECTION_POOL_EXHAUSTED",
            "HikariPool-1 timed out after 30000ms waiting for connection",
            "Active connections: 50/50, Waiting requests: 87",
            "Order API error rate spiked to 64% with p99 latency > 30s"
        ],
        "recommended_actions": [
            "Run 'SELECT * FROM pg_stat_activity WHERE state != ''idle''' in PostgreSQL to identify hung or slow transactions.",
            "Terminate blocking batch queries using 'SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE duration > interval ''30 seconds''.",
            "Increase HikariCP pool size in configuration (SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE=100).",
            "Configure leakDetectionThreshold=5000ms and connectionTimeout=15000ms to detect unclosed connection leaks early.",
            "Restart the orders-api worker service and resume the blocked BPMN instances in Camunda Operate."
        ],
        "confidence": "HIGH",
        "source": "predefined_sre_runbook",
        "use_count": 1
    },
    {
        "error_type": "KAFKA_TIMEOUT",
        "process_id": "order-fulfillment-process",
        "summary": "Kafka producer batch delivery timeout due to broker disconnect or partition leader loss.",
        "root_cause": "The Kafka producer in 'event-bridge' failed to deliver 148 records to topic 'order-events-0' within 120000ms. A broker node rolling restart or network partition caused producer buffer saturation (96% full) and backpressure failure.",
        "observed_facts": [
            "Error type is KAFKA_TIMEOUT",
            "Connection to Kafka node 3 (broker-3:9092) failed",
            "Batch delivery timeout after 120000ms on topic 'order-events-0'",
            "Producer buffer 96% full with 148 pending records dropped"
        ],
        "recommended_actions": [
            "Verify Kafka cluster health and broker connectivity using 'kafka-broker-api-versions.sh --bootstrap-server localhost:9092'.",
            "Check partition leader and ISR list: 'kafka-topics.sh --describe --topic order-events --bootstrap-server localhost:9092'.",
            "Ensure min.insync.replicas=2 and enough healthy brokers are online to satisfy acks=all.",
            "Tune producer resilience settings: increase delivery.timeout.ms=180000 and max.block.ms=30000.",
            "Clear backpressure on the event-bridge service and retry the failed service task in Camunda Operate."
        ],
        "confidence": "HIGH",
        "source": "predefined_sre_runbook",
        "use_count": 1
    },
    {
        "error_type": "HTTP_500",
        "process_id": "checkout-process",
        "summary": "Upstream external payment provider service returned HTTP 500 Internal Server Error.",
        "root_cause": "The payment gateway worker 'ServiceTask_ChargeCard' received a 500 Internal Server Error from upstream provider 'api.pay-provider.io/v1/charges'. The worker exhausted all automated retries (retries=0), causing a Zeebe JOB_NO_RETRIES incident.",
        "observed_facts": [
            "Error type is HTTP_500 / JOB_NO_RETRIES",
            "Payment gateway returned 500 Internal Server Error for POST /charges",
            "Worker job retries reached 0 on ServiceTask_ChargeCard",
            "Checkout process instance is stalled awaiting manual resolution"
        ],
        "recommended_actions": [
            "Check upstream payment provider status page (api.pay-provider.io) for active platform incidents.",
            "Inspect payment gateway worker logs for provider-specific error codes (e.g. gateway timeout, database error).",
            "Implement a Circuit Breaker (e.g. Resilience4j / Envoy) to fail fast and route to a fallback payment provider during outages.",
            "Once upstream provider confirms recovery, update incident retries from 0 to 3 in Camunda Operate.",
            "Resolve the incident in Camunda Operate to allow the checkout workflow to complete."
        ],
        "confidence": "HIGH",
        "source": "predefined_sre_runbook",
        "use_count": 1
    },
    {
        "error_type": "EXTRACT_VALUE_ERROR",
        "process_id": "*",
        "summary": "FEEL expression or variable extraction failed because the referenced variable is null or missing.",
        "root_cause": "A FEEL expression attempted to read or extract a variable that does not exist in the current process execution scope, or evaluated an undefined property on a null object.",
        "observed_facts": [
            "Error type is EXTRACT_VALUE_ERROR",
            "FEEL expression evaluation failed at runtime",
            "Referenced variable or property is null or not in scope"
        ],
        "recommended_actions": [
            "Identify the failing FEEL expression from the element ID in the Camunda incident.",
            "Inspect process variables at the point of failure to verify if required variables were initialized.",
            "Add null-coalescing defaults in FEEL expressions: if myVar != null then myVar else 'default'.",
            "Correct any variable name typos in BPMN input/output variable mappings.",
            "Redeploy the updated BPMN process definition and retry the incident in Camunda Operate."
        ],
        "confidence": "HIGH",
        "source": "predefined_sre_runbook",
        "use_count": 1
    },
    {
        "error_type": "IO_MAPPING_ERROR",
        "process_id": "*",
        "summary": "Input/Output variable mapping between BPMN elements failed due to type incompatibility or missing source.",
        "root_cause": "The task I/O mapping configuration could not map the source expression to the target variable. The source variable is either null, does not exist, or has an incompatible data type.",
        "observed_facts": [
            "Error type is IO_MAPPING_ERROR",
            "Task I/O variable mapping failed",
            "Source variable is null, missing, or type incompatible"
        ],
        "recommended_actions": [
            "Check the Input/Output mapping configuration on the failing task in Camunda Modeler.",
            "Verify all source variables exist and have expected data types prior to task execution.",
            "Add defensive null-checks or default values for optional source variables in FEEL mappings.",
            "Redeploy the BPMN model and retry the process instance in Camunda Operate."
        ],
        "confidence": "HIGH",
        "source": "predefined_sre_runbook",
        "use_count": 1
    }
]

def seed():
    print(f"Connecting to Supabase at {SUPABASE_URL}...")
    if not is_configured():
        print("Error: Supabase is not configured.")
        return

    # Delete existing seeded template rows to ensure fresh predefined runbooks
    import urllib.request
    from supabase_runbook import _headers
    try:
        req = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/{TABLE}?instance_key=is.null", headers=_headers(), method="DELETE")
        urllib.request.urlopen(req)
        print("  [INFO] Cleared previous generic runbooks")
    except Exception as e:
        print(f"  [INFO] Cleaned table ({e})")

    seeded_count = 0
    for rb in PREDEFINED_RUNBOOKS:
        error_type = rb["error_type"]
        proc_id    = rb["process_id"]
        res = _post(TABLE, rb)
        if res:
            print(f"  [OK] Seeded runbook: [{error_type}] (process: {proc_id})")
            seeded_count += 1
        else:
            print(f"  [WARN] Failed to seed [{error_type}]")

    print(f"\nSeeding complete! {seeded_count}/{len(PREDEFINED_RUNBOOKS)} predefined runbooks are active in Supabase.")

if __name__ == "__main__":
    seed()
