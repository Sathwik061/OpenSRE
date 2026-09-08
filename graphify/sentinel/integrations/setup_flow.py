"""
sentinel/integrations/setup_flow.py
===================================
Setup validation and execution pipeline for onboarding OpenSRE integrations.
Coordinates field validation, connectivity verification, and encrypted storage.
"""

from typing import Dict, Any, Tuple
from sentinel.integrations.catalog import get_integration_def
from sentinel.integrations.verifier_base import PingResult, DefaultRestVerifier, BaseIntegrationVerifier
from sentinel.integrations.secrets_vault import secrets_vault


class SetupFlowManager:
    def __init__(self):
        self._custom_verifiers: Dict[str, BaseIntegrationVerifier] = {}

    def register_verifier(self, integration_id: str, verifier: BaseIntegrationVerifier) -> None:
        self._custom_verifiers[integration_id] = verifier

    def get_verifier(self, integration_id: str) -> BaseIntegrationVerifier:
        return self._custom_verifiers.get(integration_id, DefaultRestVerifier())

    def validate_fields(self, integration_id: str, credentials: Dict[str, Any]) -> Tuple[bool, str]:
        """Verify all required fields defined in catalog are supplied."""
        definition = get_integration_def(integration_id)
        if not definition:
            return False, f"Integration '{integration_id}' is not recognized in catalog."

        for field in definition.get("required_fields", []):
            if field.get("required") and not credentials.get(field["key"]):
                return False, f"Missing required configuration field: '{field.get('label', field['key'])}'."

        return True, "All required fields supplied."

    async def test_and_configure(
        self,
        integration_id: str,
        credentials: Dict[str, Any],
        save_to_vault: bool = True
    ) -> PingResult:
        """
        Validate fields, run connectivity ping, and optionally store in encrypted vault.
        """
        is_valid, err_msg = self.validate_fields(integration_id, credentials)
        if not is_valid:
            return PingResult(
                success=False,
                status_code=400,
                message=err_msg,
                details={"error": err_msg}
            )

        verifier = self.get_verifier(integration_id)
        result = await verifier.verify(credentials)

        if result.success and save_to_vault:
            secrets_vault.store_credentials(integration_id, credentials)

        return result


setup_manager = SetupFlowManager()
