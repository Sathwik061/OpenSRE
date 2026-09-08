"""
sentinel/integrations/adapters/datadog_adapter.py
================================================
Datadog APM & Metrics Integration Adapter for OpenSRE.
Supports:
  - Auth validation against Datadog /api/v1/validate
  - Live metric and APM error spike correlation
"""

import time
import httpx
from typing import Dict, Any
from sentinel.integrations.verifier_base import BaseIntegrationVerifier, PingResult


class DatadogVerifier(BaseIntegrationVerifier):
    async def verify(self, credentials: Dict[str, Any]) -> PingResult:
        start_time = time.time()
        api_key = credentials.get("api_key", "").strip()
        app_key = credentials.get("app_key", "").strip()
        site = credentials.get("site", "datadoghq.com").strip() or "datadoghq.com"

        if not api_key or not app_key:
            return PingResult(success=False, message="Both 'api_key' and 'app_key' are required.")

        url = f"https://api.{site}/api/v1/validate"
        headers = {
            "DD-API-KEY": api_key,
            "DD-APPLICATION-KEY": app_key,
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, headers=headers)
                latency = (time.time() - start_time) * 1000.0
                if resp.status_code == 200 and resp.json().get("valid"):
                    return PingResult(
                        success=True,
                        latency_ms=round(latency, 2),
                        status_code=200,
                        message=f"Datadog API keys validated successfully on {site}.",
                        details={"site": site, "valid": True}
                    )
                else:
                    return PingResult(
                        success=False,
                        latency_ms=round(latency, 2),
                        status_code=resp.status_code,
                        message=f"Datadog authentication failed: {resp.text[:200]}",
                        details={"status": resp.status_code}
                    )
        except Exception as e:
            return PingResult(
                success=False,
                latency_ms=round((time.time() - start_time) * 1000.0, 2),
                status_code=502,
                message=f"Failed to connect to Datadog API: {str(e)}",
                details={"error": str(e), "site": site}
            )
