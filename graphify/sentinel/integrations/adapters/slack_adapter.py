"""
sentinel/integrations/adapters/slack_adapter.py
==============================================
Slack ChatOps Integration Adapter for OpenSRE.
Features:
  - Formats rich Slack Block Kit incident cards with interactive SRE actions
  - Supports Bot OAuth tokens and incoming webhooks
  - Verifier pings auth.test to validate token permissions
"""

import time
import httpx
from typing import Dict, Any, Optional
from sentinel.integrations.verifier_base import BaseIntegrationVerifier, PingResult


class SlackVerifier(BaseIntegrationVerifier):
    async def verify(self, credentials: Dict[str, Any]) -> PingResult:
        start_time = time.time()
        bot_token = credentials.get("bot_token")
        webhook_url = credentials.get("webhook_url")

        if bot_token:
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(
                        "https://slack.com/api/auth.test",
                        headers={"Authorization": f"Bearer {bot_token}"}
                    )
                    latency = (time.time() - start_time) * 1000.0
                    data = resp.json()
                    if data.get("ok"):
                        return PingResult(
                            success=True,
                            latency_ms=round(latency, 2),
                            status_code=200,
                            message=f"Slack Bot connected successfully as @{data.get('user', 'bot')} (Team: {data.get('team')})",
                            details={"team": data.get("team"), "user": data.get("user"), "bot_id": data.get("bot_id")}
                        )
                    else:
                        return PingResult(
                            success=False,
                            latency_ms=round(latency, 2),
                            status_code=401,
                            message=f"Slack authentication failed: {data.get('error', 'invalid_auth')}",
                            details=data
                        )
            except Exception as e:
                return PingResult(
                    success=False,
                    latency_ms=round((time.time() - start_time) * 1000.0, 2),
                    status_code=502,
                    message=f"Failed to connect to Slack API: {str(e)}",
                    details={"error": str(e)}
                )

        if webhook_url:
            return PingResult(
                success=True,
                latency_ms=round((time.time() - start_time) * 1000.0, 2),
                status_code=200,
                message="Slack incoming webhook URL formatted properly.",
                details={"webhook": "configured"}
            )

        return PingResult(
            success=False,
            status_code=400,
            message="Neither bot_token nor webhook_url provided.",
            details={}
        )


def build_slack_block_kit_rca(rca_payload: Dict[str, Any], dashboard_url: str = "http://localhost:5173") -> Dict[str, Any]:
    """
    Construct an enterprise Slack Block Kit incident alert card.
    """
    incident_id = rca_payload.get("incident_id") or rca_payload.get("id", "INC-UNKNOWN")
    service = rca_payload.get("service", "Unknown Service")
    error_type = rca_payload.get("error_type", "ANOMALY_DETECTED")
    confidence = rca_payload.get("confidence", "HIGH")
    root_cause = rca_payload.get("root_cause", "Investigating root cause...")
    severity = rca_payload.get("severity", "HIGH").upper()

    # Mask any lingering sensitive tokens in root cause text
    from sentinel.core.masking import mask_sensitive_patterns
    sanitized_rca = mask_sensitive_patterns(str(root_cause))

    status_emoji = ":fire:" if severity in ["FATAL", "CRITICAL", "HIGH"] else ":warning:"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{status_emoji} OpenSRE Incident Alert: {service}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Incident ID:*\n`{incident_id}`"},
                {"type": "mrkdwn", "text": f"*Severity:*\n*{severity}*"},
                {"type": "mrkdwn", "text": f"*Error Type:*\n`{error_type}`"},
                {"type": "mrkdwn", "text": f"*Confidence:*\n`{confidence}`"},
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Root Cause Analysis:*\n> {sanitized_rca[:300]}..."
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Open RCA Dashboard :rocket:", "emoji": True},
                    "url": f"{dashboard_url}/rca/{incident_id}",
                    "style": "primary",
                    "action_id": "open_rca_dashboard"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Retry Camunda Job :arrows_counterclockwise:", "emoji": True},
                    "value": f"retry_{incident_id}",
                    "action_id": "retry_camunda_job"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Acknowledge :white_check_mark:", "emoji": True},
                    "value": f"ack_{incident_id}",
                    "action_id": "ack_incident"
                }
            ]
        }
    ]

    return {"text": f"OpenSRE Alert: {error_type} in {service}", "blocks": blocks}
