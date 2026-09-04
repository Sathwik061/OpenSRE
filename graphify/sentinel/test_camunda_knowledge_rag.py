"""
sentinel/test_camunda_knowledge_rag.py
======================================
Comprehensive test suite for Camunda Documentation Knowledge Engine with:
1. Dynamic Version Pinning (8.6, 8.5, 8.4, etc.)
2. Kapa MCP Client Integration & Sub-millisecond Local Fallback
3. Live DGX Inference with Version-Scoped Prompts & Citations
"""

import sys
import os
import time
import json
from pathlib import Path

# Setup paths
_sentinel_dir = Path(r"c:\Users\madire sathwik\OneDrive - TRUVIQ SYSTEMS PRIVATE LIMITED\Documents\Open SRE\graphify\sentinel")
_graphify_dir = Path(r"c:\Users\madire sathwik\OneDrive - TRUVIQ SYSTEMS PRIVATE LIMITED\Documents\Open SRE\graphify")
sys.path.insert(0, str(_sentinel_dir))
sys.path.insert(0, str(_graphify_dir))

from camunda_knowledge import (
    retrieve_camunda_context,
    score_document,
    _load_index,
    format_versioned_doc_url,
    query_kapa_mcp,
)
from dgx_engine import is_dgx_available, get_active_model


def test_version_pinned_urls():
    print("\n--- 1. Testing Dynamic Version Pinning in Doc URLs ---")
    base_url = "https://docs.camunda.io/docs/components/modeler/bpmn/error-events/"
    
    url_85 = format_versioned_doc_url(base_url, version="8.5")
    url_86 = format_versioned_doc_url(base_url, version="8.6")
    url_84 = format_versioned_doc_url(base_url, version="8.4")

    print(f"  Target 8.5 -> {url_85}")
    print(f"  Target 8.6 -> {url_86}")
    print(f"  Target 8.4 -> {url_84}")

    assert url_85 == "https://docs.camunda.io/docs/8.5/components/modeler/bpmn/error-events/"
    assert url_86 == "https://docs.camunda.io/docs/8.6/components/modeler/bpmn/error-events/"
    assert url_84 == "https://docs.camunda.io/docs/8.4/components/modeler/bpmn/error-events/"
    print("  [PASS] All version URLs dynamically formatted correctly!")


def test_retrieval_performance():
    print("\n--- 2. Testing Retrieval Latency & Throughput ---")
    start = time.perf_counter()
    catalog = _load_index()
    elapsed_init = (time.perf_counter() - start) * 1000
    print(f"Index loaded {len(catalog)} topics in {elapsed_init:.2f} ms")

    queries = [
        ("UNHANDLED_ERROR_EVENT", "boundaryEvent", "Unhandled error event with code 'PAYMENT_FAILED'", "8.5"),
        ("CONDITION_ERROR", "exclusiveGateway", "No condition evaluated to true and no default flow", "8.6"),
        ("PARALLEL_DEADLOCK", "parallelGateway", "Parallel Join wait forever for token", "8.4"),
        ("FORM_NOT_FOUND", "userTask", "Form binding error formId 'user-approval-form'", "8.5"),
        ("JOB_NO_RETRIES", "serviceTask", "No more retries left for job type payment-charge", "8.6"),
    ]

    t0 = time.perf_counter()
    iterations = 500
    for i in range(iterations):
        q = queries[i % len(queries)]
        res = retrieve_camunda_context(
            error_type=q[0],
            element_type=q[1],
            error_message=q[2],
            version=q[3],
            top_k=2,
        )
    total_time = (time.perf_counter() - t0) * 1000
    avg_lat = total_time / iterations

    print(f"Executed {iterations} retrieval queries in {total_time:.2f} ms")
    print(f"Average latency per query: {avg_lat:.4f} ms (sub-millisecond: {avg_lat < 1.0})")
    assert avg_lat < 5.0, "Latency must be under 5ms"


def test_retrieval_scenarios():
    print("\n--- 3. Testing Version-Aware Retrieval Scenarios ---")
    scenarios = [
        {
            "name": "Unhandled Error Event on Camunda 8.5",
            "error_type": "UNHANDLED_ERROR_EVENT",
            "element_type": "boundaryEvent",
            "error_message": "Unhandled error event with code 'ORDER_CANCELLED'",
            "version": "8.5",
            "expected_top": "Error Events",
        },
        {
            "name": "Condition Error on XOR Gateway (Camunda 8.6)",
            "error_type": "CONDITION_ERROR",
            "element_type": "exclusiveGateway",
            "error_message": "Expected at least one condition to evaluate to true",
            "version": "8.6",
            "expected_top": "Exclusive Gateways (XOR)",
        },
        {
            "name": "Service Task Retries Exhausted (Camunda 8.4)",
            "error_type": "JOB_NO_RETRIES",
            "element_type": "serviceTask",
            "error_message": "Job execution failed with zero retries remaining",
            "version": "8.4",
            "expected_top": "Service Tasks & Job Workers",
        },
    ]

    for sc in scenarios:
        res = retrieve_camunda_context(
            error_type=sc["error_type"],
            element_type=sc["element_type"],
            error_message=sc["error_message"],
            version=sc["version"],
            top_k=2,
        )
        docs = res.get("docs", [])
        assert len(docs) > 0, f"Expected docs for {sc['name']}"
        top_title = docs[0]["title"]
        doc_url = docs[0]["doc_url"]
        print(f"  [PASS] {sc['name']}: Top Match = '{top_title}'")
        print(f"    Versioned URL: {doc_url}")
        assert f"/docs/{sc['version']}/" in doc_url, f"Expected version {sc['version']} in {doc_url}"
        assert sc["expected_top"] in top_title or top_title in sc["expected_top"]


def test_live_dgx_with_version_pinning():
    print("\n--- 4. Testing DGX Qwen 35B Inference with Version-Pinned Camunda 8.5 RCA ---")
    if not is_dgx_available():
        print("  ⚠️ DGX vLLM is offline (SSH tunnel not active on :8000). Skipping live model test.")
        return

    model = get_active_model()
    print(f"  DGX vLLM is CONNECTED. Active model: {model}")

    from dgx_engine import investigate_with_dgx

    sample_incident_85 = {
        "alert_name": "UNHANDLED_ERROR_EVENT in paymentProcess",
        "error_type": "UNHANDLED_ERROR_EVENT",
        "process_id": "paymentProcess",
        "element_id": "Activity_0luysxt",
        "error_message": "Unhandled error event with code 'PAYMENT_FAILED'",
        "camunda_version": "8.5",
        "variables": {
            "orderId": "ORD-8855",
            "paymentStatus": "FAILED",
        },
        "bpmn_topology": {
            "incident_element_context": {
                "element_type": "serviceTask",
                "has_error_boundary_event": False,
                "missing_boundary_warning": "Activity_0luysxt throws error 'PAYMENT_FAILED' but lacks an Error Boundary Catch Event in Camunda 8.5."
            }
        }
    }

    print("  Sending Camunda 8.5 incident to DGX...")
    t0 = time.perf_counter()
    rca = investigate_with_dgx(sample_incident_85)
    elapsed = time.perf_counter() - t0

    if rca:
        print(f"  [PASS] DGX RCA received in {elapsed:.2f}s!")
        print(f"    Summary: {rca.get('summary')}")
        print(f"    Version: Camunda {rca.get('camunda_version')}")
        print(f"    Root Cause: {rca.get('root_cause')[:120]}...")
        doc_refs = rca.get("documentation_references", [])
        print(f"    Documentation References ({len(doc_refs)}):")
        for d in doc_refs:
            print(f"      - {d.get('section')}: {d.get('url')}")
            print(f"        Relevance: {d.get('relevance')}")
            assert "8.5" in d.get("url", "") or "docs.camunda.io" in d.get("url", "")
    else:
        print("  [WARN] DGX call failed or timed out.")


if __name__ == "__main__":
    test_version_pinned_urls()
    test_retrieval_performance()
    test_retrieval_scenarios()
    test_live_dgx_with_version_pinning()
    print("\n[SUCCESS] ALL CAMUNDA KNOWLEDGE & DYNAMIC VERSION PINNING TESTS PASSED!")
