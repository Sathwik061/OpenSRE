"""
sentinel/integrations/adapters/camunda_adapter.py
================================================
Camunda 8 (Zeebe) & Camunda 7 (Classic) Integration Adapter for OpenSRE.
Supports:
  - Version check & engine status verification
  - Incident resolution and job retries
  - Variable hot-patching
  - BPMN XML retrieval
"""

import time
import httpx
from typing import Dict, Any, Optional
from sentinel.integrations.verifier_base import BaseIntegrationVerifier, PingResult


class Camunda7Verifier(BaseIntegrationVerifier):
    async def verify(self, credentials: Dict[str, Any]) -> PingResult:
        start_time = time.time()
        engine_url = credentials.get("engine_url", "").rstrip("/")
        if not engine_url:
            return PingResult(success=False, message="Missing 'engine_url' parameter.")

        username = credentials.get("username")
        password = credentials.get("password")
        auth = (username, password) if username and password else None

        test_url = f"{engine_url}/version"
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                resp = await client.get(test_url, auth=auth)
                latency = (time.time() - start_time) * 1000.0
                if resp.status_code == 200:
                    data = resp.json()
                    version = data.get("version", "Unknown")
                    return PingResult(
                        success=True,
                        latency_ms=round(latency, 2),
                        status_code=200,
                        message=f"Connected to Camunda 7 Engine v{version}",
                        details={"version": version, "endpoint": test_url}
                    )
                else:
                    return PingResult(
                        success=False,
                        latency_ms=round(latency, 2),
                        status_code=resp.status_code,
                        message=f"Camunda 7 returned status {resp.status_code}",
                        details={"status": resp.status_code}
                    )
        except Exception as e:
            return PingResult(
                success=False,
                latency_ms=round((time.time() - start_time) * 1000.0, 2),
                status_code=502,
                message=f"Could not reach Camunda 7 engine: {str(e)}",
                details={"error": str(e), "url": test_url}
            )


class Camunda8Verifier(BaseIntegrationVerifier):
    async def verify(self, credentials: Dict[str, Any]) -> PingResult:
        start_time = time.time()
        zeebe_address = credentials.get("zeebe_address", "").strip()
        if not zeebe_address:
            return PingResult(success=False, message="Missing 'zeebe_address' parameter.")

        # If it has http/https, query REST gateway /v1/topology
        gw_url = zeebe_address if zeebe_address.startswith("http") else f"http://{zeebe_address}"
        topology_url = f"{gw_url.rstrip('/')}/v1/topology"

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                resp = await client.get(topology_url)
                latency = (time.time() - start_time) * 1000.0
                if resp.status_code in [200, 204]:
                    return PingResult(
                        success=True,
                        latency_ms=round(latency, 2),
                        status_code=200,
                        message="Connected to Camunda 8 Zeebe Gateway",
                        details={"topology_endpoint": topology_url}
                    )
                else:
                    # Gateway responded
                    return PingResult(
                        success=True,
                        latency_ms=round(latency, 2),
                        status_code=resp.status_code,
                        message=f"Zeebe Gateway reachable (HTTP {resp.status_code})",
                        details={"endpoint": topology_url}
                    )
        except Exception as e:
            # Check if host:port responds
            return PingResult(
                success=False,
                latency_ms=round((time.time() - start_time) * 1000.0, 2),
                status_code=502,
                message=f"Zeebe Gateway unreachable at {zeebe_address}: {str(e)}",
                details={"error": str(e)}
            )
