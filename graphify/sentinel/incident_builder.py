from datetime import datetime, timezone
from models import IncidentAlert, ErrorEvent


def build_incident_from_error(event: ErrorEvent) -> IncidentAlert:
    """
    Converts a raw ErrorEvent (from Camunda or a webhook) into a
    fully-formed OpenSRE-compatible IncidentAlert.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build a basic timeline from the provided logs
    timeline = []
    for log in event.logs:
        # Use the first 25 chars as a timeline entry if no explicit timeline given
        entry = log[:80].strip()
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
        error_message=event.error_message,
        logs=event.logs,
        timeline=timeline,
        timestamp=timestamp,
    )
