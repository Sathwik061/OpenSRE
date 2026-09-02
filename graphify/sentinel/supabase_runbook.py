"""
supabase_runbook.py -- Supabase-backed Instance RCA & Runbook Store
===================================================================
Provides instance-level deterministic RCA persistence:
1. If the SAME instance occurs or is queried again, returns its exact saved RCA (100% consistent story).
2. If a DIFFERENT instance occurs with the same error type, it gets its own fresh DGX analysis tailored to its specific variables.
3. Standard runbook guidelines (SOPs) are used to ground DGX remediation without overwriting instance-specific facts.

Zero external dependencies -- pure Python stdlib urllib.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional

log = logging.getLogger("supabase.runbook")

# ── Configuration ─────────────────────────────────────────────────────────────
_RAW_URL = os.getenv("SUPABASE_URL", "https://tcpcjddmnyqklvqvoeat.supabase.co")

if "supabase.com/dashboard" in _RAW_URL:
    _project_ref = _RAW_URL.rstrip("/").split("/")[-1]
    SUPABASE_URL = f"https://{_project_ref}.supabase.co"
else:
    SUPABASE_URL = _RAW_URL.rstrip("/")

SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_Q8Ry2COEiLIJa3V3dLhiXg_wGHz4m4e")
TABLE   = "runbooks"
TIMEOUT = 8


def _headers() -> dict:
    """Supabase PostgREST auth headers."""
    return {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "return=representation",
    }


def _get(path: str, params: str = "") -> Optional[list]:
    """GET from Supabase PostgREST."""
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    if params:
        url = f"{url}?{params}"
    try:
        req = urllib.request.Request(url, headers=_headers(), method="GET")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:200]
        log.warning(f"Supabase GET {path} HTTP {e.code}: {body}")
        return None
    except Exception as e:
        log.warning(f"Supabase GET {path} failed: {e}")
        return None


def _post(path: str, body: dict, on_conflict: str = "") -> Optional[dict]:
    """POST/upsert to Supabase PostgREST."""
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    if on_conflict:
        url = f"{url}?on_conflict={on_conflict}"
    try:
        data = json.dumps(body).encode("utf-8")
        headers = dict(_headers())
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            result = json.loads(r.read().decode("utf-8"))
            return result[0] if isinstance(result, list) and result else result
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        log.warning(f"Supabase POST {path} HTTP {e.code}: {body}")
        return None
    except Exception as e:
        log.warning(f"Supabase POST {path} failed: {e}")
        return None


def _patch(path: str, body: dict, params: str = "") -> Optional[dict]:
    """PATCH an existing row."""
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    if params:
        url = f"{url}?{params}"
    try:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=_headers(), method="PATCH")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            result = json.loads(r.read().decode("utf-8"))
            return result[0] if isinstance(result, list) and result else result
    except Exception as e:
        log.warning(f"Supabase PATCH {path} failed: {e}")
        return None


def is_configured() -> bool:
    """Return True if Supabase credentials are set."""
    return bool(SUPABASE_URL and SUPABASE_KEY)


def health_check() -> bool:
    """Verify Supabase is reachable."""
    result = _get(TABLE, "limit=1&select=id")
    return result is not None


# ── 1. Instance-Specific Lookup (Stick to Instance) ──────────────────────────

def lookup_instance_rca(instance_key: str, incident_key: str = "") -> Optional[dict]:
    """
    Look up previously saved RCA for THIS specific instance or incident key.
    Guarantees that if the SAME instance is run/queried multiple times,
    it returns the exact same result without regenerating a different story.
    """
    if not is_configured():
        return None

    # Try lookup by instance_key first
    if instance_key:
        inst_enc = urllib.parse.quote(str(instance_key))
        rows = _get(TABLE, f"instance_key=eq.{inst_enc}&select=*&limit=1")
        if rows:
            row = rows[0]
            log.info(f"🔁 INSTANCE HIT: Found existing RCA for Instance [{instance_key}] in Supabase (100% consistent)")
            _bump_use_count(row.get("id"))
            return _row_to_rca(row)

    # Try lookup by incident_key
    if incident_key:
        inc_enc = urllib.parse.quote(str(incident_key))
        rows = _get(TABLE, f"incident_key=eq.{inc_enc}&select=*&limit=1")
        if rows:
            row = rows[0]
            log.info(f"🔁 INCIDENT HIT: Found existing RCA for Incident [{incident_key}] in Supabase (100% consistent)")
            _bump_use_count(row.get("id"))
            return _row_to_rca(row)

    return None


def _row_to_rca(row: dict) -> dict:
    return {
        "summary":             row.get("summary", ""),
        "root_cause":          row.get("root_cause", ""),
        "confidence":          row.get("confidence", "HIGH"),
        "observed_facts":      row.get("observed_facts", []),
        "recommended_actions": row.get("recommended_actions", []),
        "error_type":          row.get("error_type", ""),
        "process_id":          row.get("process_id", ""),
        "_from_instance_store": True,
        "_supabase_id":        row.get("id"),
        "_instance_key":       row.get("instance_key"),
        "_incident_key":       row.get("incident_key"),
    }


def _bump_use_count(row_id: Optional[str]) -> None:
    if not row_id:
        return
    try:
        # Non-blocking increment
        _patch(TABLE, {"use_count": 2}, f"id=eq.{row_id}")
    except Exception:
        pass


# ── 2. Save Instance-Specific RCA to Supabase ─────────────────────────────────

def save_instance_rca(
    instance_key: str,
    incident_key: str,
    error_type:   str,
    process_id:   str,
    rca:          dict,
    incident:     Optional[dict] = None,
) -> Optional[dict]:
    """
    Persist an instance-specific RCA in Supabase.
    Future queries for this instance will return this exact saved result.
    """
    if not is_configured() or not rca:
        return None

    row = {
        "instance_key":         str(instance_key or ""),
        "incident_key":         str(incident_key or ""),
        "error_type":           error_type,
        "process_id":           process_id or "*",
        "summary":              rca.get("summary", ""),
        "root_cause":           rca.get("root_cause", ""),
        "confidence":           rca.get("confidence", "HIGH"),
        "observed_facts":       rca.get("observed_facts", []),
        "recommended_actions":  rca.get("recommended_actions", []),
        "source":               "ai_generated",
        "use_count":            1,
    }

    result = _post(TABLE, row)
    if result:
        log.info(f"💾 Persisted RCA to Supabase for Instance [{instance_key}] (Error: {error_type})")
    return result


# ── 3. SOP Runbook Guidelines (General Best Practices for DGX Prompt) ─────────

def lookup_sop_guidelines(error_type: str) -> Optional[dict]:
    """
    Look up standard team SOP guidelines for an error type (where instance_key is null/global).
    Used as context to guide DGX without hardcoding instance variables.
    """
    if not is_configured():
        return None
    et_enc = urllib.parse.quote(error_type)
    rows = _get(TABLE, f"error_type=eq.{et_enc}&instance_key=is.null&select=*&limit=1")
    if not rows:
        rows = _get(TABLE, f"error_type=eq.{et_enc}&process_id=eq.*&select=*&limit=1")
    if rows:
        return rows[0]
    return None


# Backward compatibility aliases
lookup_runbook = lookup_instance_rca
save_runbook   = save_instance_rca


def list_runbooks() -> list:
    """Return all stored instance records and runbooks from Supabase."""
    rows = _get(TABLE, "select=*&order=created_at.desc")
    return rows or []


def delete_runbook(runbook_id: str) -> bool:
    """Delete a record by UUID."""
    url = f"{SUPABASE_URL}/rest/v1/{TABLE}?id=eq.{runbook_id}"
    try:
        req = urllib.request.Request(url, headers=_headers(), method="DELETE")
        with urllib.request.urlopen(req, timeout=TIMEOUT):
            return True
    except Exception as e:
        log.warning(f"Supabase DELETE {runbook_id} failed: {e}")
        return False
