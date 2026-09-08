"""
sentinel/api/integration_routes.py
==================================
FastAPI endpoints for managing the 60+ enterprise integrations,
running test pings, securely persisting credentials in the 3-tier vault,
and dispatching RCA notifications.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel

from sentinel.integrations.catalog import get_catalog, get_integration_def
from sentinel.integrations.secrets_vault import secrets_vault
from sentinel.integrations.setup_flow import setup_manager
# Import adapters to ensure all custom verifiers are registered
import sentinel.integrations.adapters  # noqa: F401

logger = logging.getLogger("sentinel.api.integrations")

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


class CredentialsPayload(BaseModel):
    credentials: Dict[str, Any]


class TestPingRequest(BaseModel):
    credentials: Optional[Dict[str, Any]] = None


@router.get("")
def list_integrations(category: Optional[str] = Query(None)):
    """
    List all integrations in the catalog, annotated with active configuration status.
    Sensitive credentials are never exposed (clean asterisk masking applied).
    """
    catalog = get_catalog()
    configured_ids = set(secrets_vault.list_configured_integrations())

    results = []
    for item in catalog:
        if category and item["category"].lower() != category.lower():
            continue
        item_id = item["id"]
        is_cfg = item_id in configured_ids
        entry = dict(item)
        entry["is_configured"] = is_cfg
        entry["configured_credentials"] = secrets_vault.get_masked_credentials(item_id) if is_cfg else None
        results.append(entry)

    return {"count": len(results), "integrations": results}


@router.get("/{integration_id}")
def get_integration(integration_id: str):
    """Retrieve full details for a single integration with safe masked credentials."""
    definition = get_integration_def(integration_id)
    if not definition:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found.")

    configured_ids = set(secrets_vault.list_configured_integrations())
    is_cfg = integration_id in configured_ids
    entry = dict(definition)
    entry["is_configured"] = is_cfg
    entry["configured_credentials"] = secrets_vault.get_masked_credentials(integration_id) if is_cfg else None
    return entry


@router.post("/{integration_id}/test")
async def test_integration(integration_id: str, payload: TestPingRequest):
    """
    Execute a live connectivity test ping using either supplied credentials
    or previously stored credentials from the encrypted vault.
    """
    credentials = payload.credentials
    if not credentials:
        # Fetch from encrypted vault
        credentials = secrets_vault.get_credentials(integration_id)
        if not credentials:
            raise HTTPException(
                status_code=400,
                detail=f"No stored credentials found for '{integration_id}', and none provided in request."
            )

    result = await setup_manager.test_and_configure(
        integration_id=integration_id,
        credentials=credentials,
        save_to_vault=False
    )
    return result.model_dump()


@router.post("/{integration_id}/configure")
async def configure_integration(integration_id: str, payload: CredentialsPayload):
    """
    Validate, ping test, and securely store integration credentials into the encrypted vault.
    """
    credentials = payload.credentials
    if not credentials:
        raise HTTPException(status_code=400, detail="Credentials payload cannot be empty.")

    result = await setup_manager.test_and_configure(
        integration_id=integration_id,
        credentials=credentials,
        save_to_vault=True
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail=f"Integration verification failed: {result.message}"
        )

    return {
        "status": "configured",
        "integration_id": integration_id,
        "verification": result.model_dump(),
        "masked_credentials": secrets_vault.get_masked_credentials(integration_id)
    }


@router.delete("/{integration_id}")
def delete_integration_configuration(integration_id: str):
    """Purge stored integration credentials from the encrypted vault."""
    deleted = secrets_vault.delete_credentials(integration_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' was not configured.")
    return {"status": "deleted", "integration_id": integration_id}


@router.post("/dispatch-rca")
async def dispatch_rca_alert(payload: Dict[str, Any] = Body(...)):
    """
    Broadcast an RCA incident alert to all configured notification channels (e.g. Slack, PagerDuty).
    """
    dispatched = []
    errors = []

    # 1. Slack Broadcast
    slack_creds = secrets_vault.get_credentials("slack")
    if slack_creds:
        try:
            from sentinel.integrations.adapters.slack_adapter import build_slack_block_kit_rca
            import httpx
            card = build_slack_block_kit_rca(payload)
            webhook_url = slack_creds.get("webhook_url")
            bot_token = slack_creds.get("bot_token")
            channel = slack_creds.get("default_channel", "#sre-war-room")

            if webhook_url:
                async with httpx.AsyncClient(timeout=6.0) as client:
                    await client.post(webhook_url, json=card)
                dispatched.append("slack_webhook")
            elif bot_token:
                async with httpx.AsyncClient(timeout=6.0) as client:
                    post_data = {"channel": channel, **card}
                    await client.post(
                        "https://slack.com/api/chat.postMessage",
                        headers={"Authorization": f"Bearer {bot_token}"},
                        json=post_data
                    )
                dispatched.append("slack_bot")
        except Exception as e:
            logger.warning(f"Failed to post to Slack: {e}")
            errors.append(f"Slack: {str(e)}")

    return {
        "dispatched_channels": dispatched,
        "errors": errors,
        "incident_id": payload.get("incident_id") or payload.get("id")
    }
