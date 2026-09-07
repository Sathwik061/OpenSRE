"""
sentinel/core/incident_builder.py
=================================
Converts raw error events into standardized IncidentAlert objects.
"""

import os
from datetime import datetime, timezone
from sentinel.core.models import IncidentAlert, ErrorEvent
from sentinel.core.masking import mask_variables, mask_string_value


def build_incident_from_error(event: ErrorEvent) -> IncidentAlert:
    """
    Converts a raw ErrorEvent (from Camunda or a webhook) into a
    fully-formed OpenSRE-compatible IncidentAlert with sensitive data masking.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    raw_vars = event.variables or (event.additional_context.get("variables") if event.additional_context else {})
    sanitized_vars = mask_variables(raw_vars) if raw_vars else None

    # Build a basic timeline from the provided logs
    timeline = []
    for log in event.logs:
        entry = mask_string_value(log[:80].strip())
        if entry:
            timeline.append(entry)

    if not timeline:
        timeline = [f"{timestamp} {event.service} error detected"]

    alert_name = (
        f"{event.service}-{event.error_type.lower().replace(' ', '-').replace('/', '-')}"
    )

    return IncidentAlert(
        alert_name=alert_name,
        service=event.service,
        environment=event.environment,
        error=event.error_type,
        error_message=mask_string_value(event.error_message),
        logs=[mask_string_value(l) for l in event.logs],
        timeline=timeline,
        timestamp=timestamp,
        camunda_version=event.camunda_version or os.getenv("CAMUNDA_VERSION", "8.9"),
        element_id=event.element_id or (event.additional_context.get("element_id") if event.additional_context else None),
        element_name=event.element_name or (event.additional_context.get("element_name") if event.additional_context else None),
        process_id=event.process_id or (event.additional_context.get("process_id") if event.additional_context else None),
        instance_key=event.instance_key or (event.additional_context.get("instance_key") if event.additional_context else None),
        incident_key=event.incident_key or (event.additional_context.get("incident_key") if event.additional_context else None),
        variables=sanitized_vars,
        bpmn_topology=event.bpmn_topology or (event.additional_context.get("bpmn_topology") if event.additional_context else None),
    )
