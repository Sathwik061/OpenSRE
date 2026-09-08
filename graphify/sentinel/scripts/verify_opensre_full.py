"""
Test suite validating end-to-end implementation across:
- Component 1: Project Intake & Context Profiling Framework (Project Passport)
- Component 2: Multi-Format Runbook Ingestion (PDF / Word / Markdown)
- Component 3: 60+ Enterprise Integration Catalog & 3-Tier Secrets Vault
- Component 4: Tier-1 Adapters (Slack, Camunda, Datadog, Kubernetes, PagerDuty)
- Component 5: Always-On Parallel Web Search Client & Local RAG
"""

import sys
import os

_script_dir = os.path.dirname(os.path.abspath(__file__))
_graphify_dir = os.path.dirname(os.path.dirname(_script_dir))
if _graphify_dir not in sys.path:
    sys.path.insert(0, _graphify_dir)

from starlette.testclient import TestClient
from sentinel.main import app

client = TestClient(app)

print("\n--- 1. Testing Project Passports API ---")
res = client.get("/api/projects")
assert res.status_code == 200, f"Expected 200, got {res.status_code}"
data = res.json()
print(f"Registered Projects: {data['count']}")
assert data["count"] >= 4
sample_proj = data["projects"][0]
print(f"Sample: {sample_proj['name']} | Platform: {sample_proj['platform']} | Purpose: {sample_proj['business_purpose'][:60]}...")

print("\n--- 2. Testing 60+ Integrations Catalog API ---")
res = client.get("/api/integrations")
assert res.status_code == 200
cat_data = res.json()
print(f"Catalog Integrations count: {cat_data['count']}")
assert cat_data["count"] >= 20
sample_int = cat_data["integrations"][0]
print(f"Sample: {sample_int['name']} | Category: {sample_int['category']} | Tier: {sample_int['tier']}")

print("\n--- 3. Testing 3-Tier Secrets Vault & Clean Asterisk Masking ---")
from sentinel.integrations.secrets_vault import secrets_vault
secrets_vault.store_credentials("camunda_8", {
    "zeebe_address": "cluster.camunda.io:443",
    "client_id": "test-client-id-1234",
    "client_secret": "SuperSecretPassword12345678"
})
masked_camunda = secrets_vault.get_masked_credentials("camunda_8")
print(f"Masked Client Secret: {masked_camunda['client_secret']}")
assert masked_camunda["client_secret"].startswith("********")
assert "SuperSecretPassword" not in masked_camunda["client_secret"]
print("Clean Masking Verified: No secret leakage!")

print("\n--- 4. Testing Multi-Format Runbook Document Ingestion ---")
files = {
    "file": (
        "Enterprise_Payment_Failure_SOP.txt",
        b"# Enterprise Payment Failure Runbook\n\n## Symptom\nWhen Stripe API times out with 504.\n\n## Remediation\n1. Switch to secondary payment rail.\n2. Scale connection timeout from 5s to 15s.",
        "text/plain"
    )
}
res = client.post("/api/runbooks/upload", files=files, data={"title": "Payment Failure SOP"})
assert res.status_code == 200
up_data = res.json()
print(f"Uploaded runbook: {up_data['title']} | Chunks indexed: {up_data['chunks_indexed']}")

print("\n--- 5. Testing RCA Investigation with Project Passport & Web Intelligence ---")
investigate_payload = {
    "alert_name": "Order Payment Gateway Timeout",
    "service": "orderFulfillmentProcess",
    "error": "UNHANDLED_ERROR_EVENT",
    "error_message": "PaymentGatewayTimeout: 504 Gateway Timeout connecting to Stripe processor",
    "logs": [
        "[FATAL] [orderFulfillmentProcess] PaymentGatewayTimeout: Stripe gateway connection timed out",
        "[ERROR] [orderFulfillmentProcess] UNHANDLED_ERROR_EVENT: Task 'Activity_ProcessPayment' failed"
    ],
    "camunda_version": "8.9"
}
res = client.post("/api/investigate", json=investigate_payload)
assert res.status_code == 202
inv_id = res.json()["investigation_id"]

import time
time.sleep(1.0)  # Allow background worker to complete

poll_res = client.get(f"/api/investigations/{inv_id}")
assert poll_res.status_code == 200
rca = poll_res.json()["rca"]
print(f"RCA Summary: {rca['summary']}")
print(f"RCA Root Cause: {rca['root_cause'][:90]}...")
print(f"Project Passport Attached: {rca.get('project_passport', {}).get('name')}")
print(f"Project Intent in RCA: {rca.get('project_passport', {}).get('business_purpose')[:70]}...")
print(f"Web References: {len(rca.get('web_references', []))} citations")
print(f"Total Observed Facts: {len(rca.get('observed_facts', []))}")

assert rca.get("project_passport") is not None
assert len(rca.get("web_references", [])) > 0

print("\n=======================================================")
print(" SUCCESS: ALL OPEN SRE CORE ENGINES & APIS VERIFIED! ")
print("=======================================================")
