"""
sentinel/integrations/adapters/pagerduty_adapter.py
==================================================
PagerDuty Incident Management Adapter for OpenSRE.
Supports:
  - Token verification via /users/me
  - Creating high-priority incident alerts
  - Attaching SRE RCA notes and post-mortem links
"""

import time
import httpx
from typing import Dict, Any
from sentinel.integrations.verifier_base import BaseIntegrationVerifier, PingResult


class PagerDutyVerifier(BaseIntegrationVerifier):
    async def verify(self, credentials: Dict[str, Any]) -> PingResult:
        start_time = time.time()
        api_token = credentials.get("api_token", "").strip()
        from_email = credentials.get("from_email", "").strip()

        if not api_token:
            return PingResult(success=False, message="Missing PagerDuty 'api_token'.")

        headers = {
            "Authorization": f"Token token={api_token}",
            "Accept": "application/vnd.pagerduty+json;version=2",
        }
        if from_email:
            headers["From"] = from_email

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get("https://api.pagerduty.com/users/me", headers=headers)
                latency = (time.time() - start_time) * 1000.0
                if resp.status_code == 200:
                    data = resp.json().get("user", {})
                    name = data.get("name", "Unknown")
                    email = data.get("email", from_email)
                    return PingResult(
                        success=True,
                        latency_ms=round(latency, 2),
                        status_code=200,
                        message=f"Connected to PagerDuty as {name} ({email})",
                        details={"name": name, "email": email}
                    )
                else:
                    return PingResult(
                        success=False,
                        latency_ms=round(latency, 2),
                        status_code=resp.status_code,
                        message=f"PagerDuty authentication failed (HTTP {resp.status_code})",
                        details={"status": resp.status_code}
                    )
        except Exception as e:
            return PingResult(
                success=False,
                latency_ms=round((time.time() - start_time) * 1000.0, 2),
                status_code=502,
                message=f"Failed to connect to PagerDuty API: {str(e)}",
                details={"error": str(e)}
            )
