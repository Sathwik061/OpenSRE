"""
sentinel/dgx_engine.py
======================
Direct integration with company NVIDIA DGX server running vLLM.
Model: nvidia/Qwen3.6-35B-A3B-NVFP4 (or whatever is served at localhost:8000)

Benefits:
  - 100% free / unlimited (runs on company DGX GPU)
  - No OpenRouter credit limits
  - High accuracy structured RCA (What, Why, Evidence, How to Fix)
  - Proven with max_tokens=4000
"""
import os
import json
import logging
import urllib.request
import urllib.error
from typing import Optional

logger = logging.getLogger("sentinel.dgx")

DGX_URL   = os.getenv("DGX_URL", "http://localhost:8000/v1")
DGX_MODEL = os.getenv("DGX_MODEL", "nvidia/Qwen3.6-35B-A3B-NVFP4")


SYSTEM_PROMPT = """You are an expert SRE (Site Reliability Engineer) Root Cause Analysis assistant.
Analyze the provided incident alert, timeline, and logs.

Strict Rules:
1. Separate OBSERVED FACTS from INFERENCES.
2. Never claim an unobserved condition as a verified fact.
3. If evidence is insufficient, explicitly state UNKNOWN.
4. The root cause must be directly supported by the supplied evidence.
5. Provide actionable remediation steps under recommended_actions.
6. Return ONLY a single valid JSON object with no surrounding markdown formatting or text.

Expected JSON Structure:
{
  "summary": "Brief summary of what failed",
  "root_cause": "Clear root cause statement",
  "confidence": "HIGH" | "MEDIUM" | "LOW",
  "observed_facts": ["fact 1", "fact 2"],
  "inferences": ["inference 1"],
  "unknowns": ["unknown 1"],
  "evidence": ["evidence 1", "evidence 2"],
  "recommended_actions": ["step 1 to fix", "step 2 to fix"]
}
"""


def is_dgx_available() -> bool:
    """Check if the local SSH tunnel to DGX vLLM is active on port 8000."""
    try:
        req = urllib.request.Request(f"{DGX_URL}/models", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def get_active_model() -> str:
    """Detect the active model name from the vLLM /models endpoint."""
    try:
        req = urllib.request.Request(f"{DGX_URL}/models", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            models = data.get("data", [])
            if models and "id" in models[0]:
                return models[0]["id"]
    except Exception:
        pass
    return DGX_MODEL


def investigate_with_dgx(incident_payload: dict) -> Optional[dict]:
    """
    Run Root Cause Analysis using company DGX vLLM endpoint.
    Returns parsed JSON dictionary or None if failed.
    """
    model_name = get_active_model()
    logger.info(f"[DGX] Querying DGX vLLM ({model_name}) at {DGX_URL}...")

    prompt_content = (
        f"Incident Alert Payload:\n"
        f"{json.dumps(incident_payload, indent=2)}\n\n"
        f"Perform strict SRE Root Cause Analysis and return valid JSON."
    )

    body = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_content},
        ],
        "max_tokens": 4000,
        "temperature": 0.1,
        # Disable chain-of-thought so content field is always populated (not reasoning)
        "chat_template_kwargs": {"enable_thinking": False},
    }

    try:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            f"{DGX_URL}/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=90) as resp:
            res_json = json.loads(resp.read().decode())

        choice = res_json.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = (message.get("content") or "").strip()

        # Fallback: if content empty, extract JSON from reasoning field
        if not content:
            reasoning = (message.get("reasoning") or "").strip()
            start_r = reasoning.find("{")
            end_r   = reasoning.rfind("}")
            if start_r != -1 and end_r != -1:
                content = reasoning[start_r:end_r+1]

        if not content:
            logger.warning("[DGX] Empty response content. Full msg: %s", str(message)[:300])
            return None

        text_to_parse = content

        # Strip any markdown code fence if present (```json ... ```)
        if text_to_parse.startswith("```"):
            lines = text_to_parse.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text_to_parse = "\n".join(lines).strip()

        # Extract JSON object (handles leading/trailing text)
        start = text_to_parse.find("{")
        end   = text_to_parse.rfind("}")
        if start != -1 and end != -1:
            text_to_parse = text_to_parse[start:end+1]

        parsed = json.loads(text_to_parse)

        # Normalize into standard RCA format expected by Graphify
        score = 0.9 if parsed.get("confidence") == "HIGH" else 0.7 if parsed.get("confidence") == "MEDIUM" else 0.5
        recs = "\n".join(f"- {a}" for a in parsed.get("recommended_actions", []))
        evid = "\n".join(f"- {e}" for e in parsed.get("evidence", []))
        facts = "\n".join(f"- {f}" for f in parsed.get("observed_facts", []))

        report_text = (
            f"### Root Cause\n{parsed.get('root_cause', 'N/A')}\n\n"
            f"### Observed Facts\n{facts}\n\n"
            f"### Cited Evidence\n{evid}\n\n"
            f"### Recommended Actions\n{recs}\n"
        )

        return {
            "summary": parsed.get("summary", ""),
            "root_cause": parsed.get("root_cause", ""),
            "validity_score": score,
            "is_noise": False,
            "confidence": parsed.get("confidence", "HIGH"),
            "observed_facts": parsed.get("observed_facts", []),
            "inferences": parsed.get("inferences", []),
            "unknowns": parsed.get("unknowns", []),
            "evidence": parsed.get("evidence", []),
            "recommended_actions": parsed.get("recommended_actions", []),
            "report": report_text,
            "engine": f"DGX ({model_name})",
        }

    except Exception as exc:
        logger.warning(f"[DGX] Investigation query failed: {exc}")
        return None
