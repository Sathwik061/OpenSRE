"""
sentinel/integrations/adapters/kubernetes_adapter.py
===================================================
Kubernetes Infrastructure Integration Adapter for OpenSRE.
Supports:
  - Cluster reachability via ServiceAccount Bearer token
  - Inspecting pod crashloops and namespace events
  - Triggering deployment rolling restarts
"""

import time
import httpx
from typing import Dict, Any
from sentinel.integrations.verifier_base import BaseIntegrationVerifier, PingResult


class KubernetesVerifier(BaseIntegrationVerifier):
    async def verify(self, credentials: Dict[str, Any]) -> PingResult:
        start_time = time.time()
        api_server = credentials.get("api_server", "").rstrip("/")
        token = credentials.get("token", "").strip()

        if not api_server:
            return PingResult(success=False, message="Missing 'api_server' URL.")

        # Strip Bearer if user accidentally included it
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

        headers = {"Authorization": f"Bearer {token}"} if token else {}
        test_url = f"{api_server}/api/v1/namespaces"

        try:
            # Many internal clusters use self-signed certs; verify=False for ping test
            async with httpx.AsyncClient(timeout=8.0, verify=False) as client:
                resp = await client.get(test_url, headers=headers)
                latency = (time.time() - start_time) * 1000.0
                if resp.status_code == 200:
                    namespaces = [item["metadata"]["name"] for item in resp.json().get("items", [])[:5]]
                    return PingResult(
                        success=True,
                        latency_ms=round(latency, 2),
                        status_code=200,
                        message=f"Connected to Kubernetes API Server ({len(namespaces)} namespaces listed)",
                        details={"namespaces": namespaces, "api_server": api_server}
                    )
                elif resp.status_code in [401, 403]:
                    return PingResult(
                        success=False,
                        latency_ms=round(latency, 2),
                        status_code=resp.status_code,
                        message=f"Kubernetes API server reachable, but token authorization failed (HTTP {resp.status_code}).",
                        details={"status": resp.status_code}
                    )
                else:
                    return PingResult(
                        success=False,
                        latency_ms=round(latency, 2),
                        status_code=resp.status_code,
                        message=f"Kubernetes returned HTTP {resp.status_code}",
                        details={"status": resp.status_code}
                    )
        except Exception as e:
            return PingResult(
                success=False,
                latency_ms=round((time.time() - start_time) * 1000.0, 2),
                status_code=502,
                message=f"Failed to connect to Kubernetes API server: {str(e)}",
                details={"error": str(e), "url": test_url}
            )
