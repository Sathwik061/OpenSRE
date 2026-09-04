"""
sentinel/knowledge/kapa_mcp_client.py
======================================
Model Context Protocol (MCP) Client for Camunda Documentation powered by Kapa.ai.
Endpoint: https://camunda-docs.mcp.kapa.ai

Features:
  - Standard JSON-RPC 2.0 protocol over HTTP
  - Dynamic version-scoped querying ([Camunda {version}])
  - Tools: 'retrieval' / 'search' and 'fetch_document'
  - Bearer token / API Key auth support via KAPA_API_KEY
  - Graceful timeout handling & structured response formatting
"""

import os
import json
import logging
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List

logger = logging.getLogger("sentinel.knowledge.kapa_mcp")

KAPA_MCP_URL = os.getenv("KAPA_MCP_URL", "https://camunda-docs.mcp.kapa.ai").rstrip("/")
KAPA_API_KEY = os.getenv("KAPA_API_KEY", "") or os.getenv("KAPA_AUTH_TOKEN", "")
KAPA_TIMEOUT = int(os.getenv("KAPA_TIMEOUT", "6"))


def is_kapa_configured() -> bool:
    """Check if Kapa API key or authorization token is set."""
    return bool(KAPA_API_KEY)


def _build_headers() -> Dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": "OpenSRE-KapaMCPClient/2.0",
    }
    if KAPA_API_KEY:
        headers["Authorization"] = f"Bearer {KAPA_API_KEY}"
    return headers


def _call_mcp_rpc(method: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Send a standard JSON-RPC 2.0 request to the Kapa MCP server."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {},
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            KAPA_MCP_URL,
            data=data,
            headers=_build_headers(),
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=KAPA_TIMEOUT) as resp:
            raw_text = resp.read().decode("utf-8")
            if raw_text.strip().startswith("data:"):
                # Handle SSE formatted responses
                for line in raw_text.splitlines():
                    if line.startswith("data:"):
                        line_data = line[5:].strip()
                        if line_data:
                            return json.loads(line_data)
            return json.loads(raw_text)
    except urllib.error.HTTPError as e:
        logger.debug(f"Kapa MCP HTTP {e.code}: {e.reason}")
        return None
    except Exception as e:
        logger.debug(f"Kapa MCP request failed: {e}")
        return None


def query_kapa_mcp(
    query: str,
    version: str = "8.9",
    top_k: int = 3,
) -> Dict[str, Any]:
    """
    Queries the Camunda Kapa MCP server with version-scoped context.
    Returns:
      {
        "docs": [ { "title", "url", "content", "summary", "score" } ],
        "prompt_section": "...",
        "citations_catalog": [ { "title", "url" } ],
        "source": "kapa_mcp"
      }
    """
    version_tag = f"Camunda {version}"
    scoped_query = f"[{version_tag}] {query}"
    logger.info(f"🌐 Querying Kapa MCP ({version_tag}): {query[:60]}...")

    # Call 'tools/call' with retrieval parameters
    rpc_res = _call_mcp_rpc("tools/call", {
        "name": "retrieval",
        "arguments": {
            "query": scoped_query,
            "top_k": top_k,
        }
    })

    if not rpc_res or "result" not in rpc_res:
        # Try fallback tool name 'search'
        rpc_res = _call_mcp_rpc("tools/call", {
            "name": "search",
            "arguments": {
                "query": scoped_query,
                "limit": top_k,
            }
        })

    if not rpc_res or "result" not in rpc_res:
        return {"docs": [], "prompt_section": "", "citations_catalog": [], "source": "kapa_mcp"}

    result_data = rpc_res.get("result", {})
    content_list = result_data.get("content", [])
    
    docs_out = []
    citations_catalog = []
    prompt_lines = [
        f"📚 OFFICIAL CAMUNDA {version} RULES & DOCUMENTATION (via Kapa MCP)",
        "============================================================",
        f"Target Engine: Camunda {version}. Use the official rules below to substantiate root cause analysis.\n"
    ]

    for idx, item in enumerate(content_list[:top_k], start=1):
        text = item.get("text", "") if isinstance(item, dict) else str(item)
        title = item.get("title") or f"Camunda {version} Documentation (Section {idx})"
        url = item.get("url") or f"https://docs.camunda.io/docs/{version}/"

        docs_out.append({
            "id": f"kapa-{idx}",
            "title": title,
            "doc_url": url,
            "score": 90.0 - (idx * 5),
            "summary": text[:200].strip() + "...",
            "content": text[:2500],
            "version": version,
        })
        citations_catalog.append({
            "title": title,
            "url": url,
            "version": version,
        })
        prompt_lines.append(f"### 📖 {title}")
        prompt_lines.append(f"Documentation URL: {url}")
        prompt_lines.append(f"Content:")
        prompt_lines.append(text[:2500])
        prompt_lines.append("\n" + "-" * 50 + "\n")

    return {
        "docs": docs_out,
        "prompt_section": "\n".join(prompt_lines) if docs_out else "",
        "citations_catalog": citations_catalog,
        "source": "kapa_mcp",
    }
