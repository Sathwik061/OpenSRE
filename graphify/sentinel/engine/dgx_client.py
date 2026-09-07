"""
sentinel/engine/dgx_client.py
=============================
Direct client for company NVIDIA DGX server running vLLM.
Model: nvidia/Qwen3.6-35B-A3B-NVFP4 (or whatever is served at localhost:8000)

Provides:
  - Fast HTTP communication over SSH tunnel
  - Auto model discovery
  - Robust 3-tier JSON parsing
  - Topology warning merging and official doc citation enrichment
"""

import os
import re
import json
import logging
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

from sentinel.engine.prompt_builder import build_rca_prompt

logger = logging.getLogger("sentinel.engine.dgx")

DGX_URL   = os.getenv("DGX_URL", "http://localhost:8000/v1").rstrip("/")
DGX_MODEL = os.getenv("DGX_MODEL", "nvidia/Qwen3.6-35B-A3B-NVFP4")


def is_dgx_available() -> bool:
    """Check if the local SSH tunnel to DGX vLLM is active on port 8000 (fast socket check < 0.3s)."""
    import socket
    try:
        # Fast TCP handshake probe (fails in ~1ms on localhost if port is closed)
        with socket.create_connection(("127.0.0.1", 8000), timeout=0.3):
            pass
        req = urllib.request.Request(f"{DGX_URL}/models", method="GET")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False


def check_dgx_alive() -> bool:
    """Alias for is_dgx_available."""
    return is_dgx_available()


def get_active_model() -> str:
    """Detect the active model name from the vLLM /models endpoint."""
    try:
        req = urllib.request.Request(f"{DGX_URL}/models", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("data", [])
            if models and "id" in models[0]:
                return models[0]["id"]
    except Exception:
        pass
    return DGX_MODEL


def _parse_llm_json(raw: str) -> Optional[Dict[str, Any]]:
    """
    Robust 3-strategy JSON parser for LLM outputs:
    1. Direct json.loads
    2. Clean trailing commas & smart quotes, then retry
    3. Regex field extraction fallback
    """
    if not raw:
        return None

    # Strip code fences
    cleaned_text = raw.strip()
    if cleaned_text.startswith("```"):
        lines = cleaned_text.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned_text = "\n".join(lines).strip()

    # Extract JSON object substring
    start = cleaned_text.find("{")
    end   = cleaned_text.rfind("}")
    if start != -1 and end != -1:
        cleaned_text = cleaned_text[start:end+1]

    # Strategy 1: Direct JSON parse
    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Clean trailing commas & unicode quotes
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned_text)
    cleaned = cleaned.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Strategy 3: Regex field extraction
    logger.warning("JSON parse failed — extracting fields via regex fallback")
    result: Dict[str, Any] = {}

    def _extract(field: str) -> str:
        m = re.search(rf'"{field}"\s*:\s*"([^"]*)"', raw, re.IGNORECASE | re.DOTALL)
        return m.group(1) if m else ""

    def _extract_list(field: str) -> list:
        m = re.search(rf'"{field}"\s*:\s*\[([^\]]*)\]', raw, re.IGNORECASE | re.DOTALL)
        if m:
            return re.findall(r'"([^"]*)"', m.group(1))
        return []

    result["summary"]             = _extract("summary")
    result["root_cause"]          = _extract("root_cause")
    result["confidence"]          = _extract("confidence") or "LOW"
    result["observed_facts"]      = _extract_list("observed_facts")
    result["recommended_actions"] = _extract_list("recommended_actions")

    doc_m = re.search(r'"documentation_references"\s*:\s*(\[[^\]]*\])', raw, re.IGNORECASE | re.DOTALL)
    if doc_m:
        try:
            result["documentation_references"] = json.loads(doc_m.group(1))
        except Exception:
            pass

    if result["summary"] or result["root_cause"]:
        return result

    return None


def run_rca_on_dgx(
    incident_payload: Dict[str, Any],
    sop_runbook: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Executes RCA on DGX Qwen 35B with BPMN topology, official docs, and SOP runbook.
    """
    model = get_active_model()
    system_prompt, user_content, retrieved_citations = build_rca_prompt(
        incident_payload=incident_payload,
        sop_runbook=sop_runbook,
    )

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content},
        ],
        "max_tokens": 2500,
        "temperature": 0.0,
        "chat_template_kwargs": {"enable_thinking": False},
    }

    try:
        data = json.dumps(body).encode("utf-8")
        req  = urllib.request.Request(
            f"{DGX_URL}/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read().decode("utf-8"))

        choice  = resp.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = (message.get("content") or "").strip()

        if not content:
            reasoning = (message.get("reasoning") or "").strip()
            start_r = reasoning.find("{")
            end_r   = reasoning.rfind("}")
            if start_r != -1 and end_r != -1:
                content = reasoning[start_r:end_r+1]

        if not content:
            logger.warning("DGX returned empty content.")
            return None

        parsed = _parse_llm_json(content)
        if not parsed:
            return None

        if not parsed.get("evidence"):
            err_msg = incident_payload.get("error_message")
            if err_msg:
                parsed["evidence"] = [err_msg]

        camunda_version = str(incident_payload.get("camunda_version") or os.getenv("CAMUNDA_VERSION", "8.9")).strip()
        parsed["camunda_version"] = camunda_version
        error_type = incident_payload.get("error_type", "")
        # Populate documentation_references if missing
        if not parsed.get("documentation_references") and retrieved_citations:
            parsed["documentation_references"] = [
                {
                    "section": c["title"],
                    "url": c["url"],
                    "relevance": f"Official Camunda {camunda_version} documentation rule for {error_type or 'this incident'}",
                    "camunda_version": camunda_version,
                }
                for c in retrieved_citations[:2]
            ]

        # Merge pre-computed BFS topology warnings
        bpmn_topology = incident_payload.get("bpmn_topology") or {}
        pre_computed  = bpmn_topology.get("warnings", []) or []
        dgx_warnings  = parsed.get("topology_warnings") or []

        if pre_computed:
            merged = list(pre_computed)
            seen = {w.lower()[:60] for w in merged}
            for w in dgx_warnings:
                if w.lower()[:60] not in seen:
                    merged.append(w)
                    seen.add(w.lower()[:60])
            parsed["topology_warnings"] = merged
        elif dgx_warnings:
            parsed["topology_warnings"] = dgx_warnings

        # Dynamically extract and ensure actionable recommendations from all detected topology warnings
        recs = parsed.get("recommended_actions") or []
        for tw in parsed.get("topology_warnings", []):
            if "RECOMMENDATION:" in str(tw):
                rec_text = str(tw).split("RECOMMENDATION:", 1)[1].strip()
                # Check if this topology recommendation is already adequately covered in recs
                if rec_text and not any(rec_text[:35].lower() in r.lower() or r[:35].lower() in rec_text.lower() for r in recs):
                    recs.append(rec_text)
        parsed["recommended_actions"] = recs

        return parsed

    except Exception as exc:
        logger.warning(f"DGX RCA failed: {exc}")
        return None


def investigate_with_dgx(incident_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Standard investigation entry point returning formatted Investigation report dictionary.
    """
    sop = None
    try:
        from sentinel.knowledge.runbook_knowledge import lookup_sop_guidelines
        err_type = incident_payload.get("error_type") or incident_payload.get("error") or ""
        proc_id  = incident_payload.get("process_id") or incident_payload.get("service") or "*"
        msg      = incident_payload.get("error_message") or ""
        logs     = incident_payload.get("logs") or []
        elem_id  = incident_payload.get("element_id") or ""
        sop = lookup_sop_guidelines(
            error_type=err_type,
            service=proc_id,
            error_message=msg,
            logs=logs,
            element_id=elem_id,
        )
    except Exception as e:
        logger.debug(f"SOP lookup in investigate_with_dgx skipped: {e}")

    parsed = run_rca_on_dgx(incident_payload, sop_runbook=sop)
    if not parsed:
        return None

    model_name = get_active_model()
    camunda_version = parsed.get("camunda_version") or incident_payload.get("camunda_version") or os.getenv("CAMUNDA_VERSION", "8.9")
    score = 0.9 if parsed.get("confidence") == "HIGH" else 0.7 if parsed.get("confidence") == "MEDIUM" else 0.5
    recs = "\n".join(f"- {a}" for a in parsed.get("recommended_actions", []))
    evid = "\n".join(f"- {e}" for e in parsed.get("evidence", []))
    facts = "\n".join(f"- {f}" for f in parsed.get("observed_facts", []))

    doc_refs = parsed.get("documentation_references", [])
    doc_refs_text = ""
    if doc_refs:
        doc_refs_text = f"\n\n### Official Camunda {camunda_version} Documentation References\n" + "\n".join(
            f"- **{d.get('section', 'Doc')}**: {d.get('url', '')} — {d.get('relevance', '')}"
            for d in doc_refs
        )

    report_text = (
        f"### Root Cause\n{parsed.get('root_cause', 'N/A')}\n\n"
        f"### Observed Facts\n{facts}\n\n"
        f"### Cited Evidence\n{evid}\n\n"
        f"### Recommended Actions\n{recs}"
        f"{doc_refs_text}\n"
    )

    return {
        "summary": parsed.get("summary", ""),
        "root_cause": parsed.get("root_cause", ""),
        "validity_score": score,
        "is_noise": False,
        "confidence": parsed.get("confidence", "HIGH"),
        "camunda_version": camunda_version,
        "documentation_references": doc_refs,
        "topology_warnings": parsed.get("topology_warnings", []),
        "observed_facts": parsed.get("observed_facts", []),
        "inferences": parsed.get("inferences", []),
        "unknowns": parsed.get("unknowns", []),
        "evidence": parsed.get("evidence", []),
        "recommended_actions": parsed.get("recommended_actions", []),
        "report": report_text,
        "engine": f"DGX ({model_name})",
    }
