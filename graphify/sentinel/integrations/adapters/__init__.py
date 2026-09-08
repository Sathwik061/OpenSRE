"""
sentinel/integrations/adapters/__init__.py
=========================================
Registers all dedicated Tier-1 verifiers into the OpenSRE SetupFlowManager.
"""

from sentinel.integrations.setup_flow import setup_manager
from sentinel.integrations.adapters.slack_adapter import SlackVerifier, build_slack_block_kit_rca
from sentinel.integrations.adapters.camunda_adapter import Camunda7Verifier, Camunda8Verifier
from sentinel.integrations.adapters.datadog_adapter import DatadogVerifier
from sentinel.integrations.adapters.kubernetes_adapter import KubernetesVerifier
from sentinel.integrations.adapters.pagerduty_adapter import PagerDutyVerifier

# Register dedicated verifiers with SetupFlowManager
setup_manager.register_verifier("slack", SlackVerifier())
setup_manager.register_verifier("camunda_7", Camunda7Verifier())
setup_manager.register_verifier("camunda_8", Camunda8Verifier())
setup_manager.register_verifier("datadog", DatadogVerifier())
setup_manager.register_verifier("kubernetes", KubernetesVerifier())
setup_manager.register_verifier("pagerduty", PagerDutyVerifier())

__all__ = [
    "SlackVerifier",
    "build_slack_block_kit_rca",
    "Camunda7Verifier",
    "Camunda8Verifier",
    "DatadogVerifier",
    "KubernetesVerifier",
    "PagerDutyVerifier",
]
