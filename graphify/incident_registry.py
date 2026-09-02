"""
incident_registry.py
Dynamic incident template registry — zero hardcoded timestamps or dates.
Every call to build_incident() generates fresh timestamps using datetime.now().
"""
from datetime import datetime, timezone


# ── Timestamp helpers (called at runtime, never hardcoded) ────────────────────

def _now() -> str:
    """Current UTC timestamp in ISO 8601 log format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _time() -> str:
    """Current UTC time as HH:MM:SS."""
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


_REQUEST = (
    "Determine what failed, identify the most likely root cause using the supplied evidence, "
    "explain the evidence, and recommend a safe remediation. Do not execute any remediation."
)


# ── Incident template builders ────────────────────────────────────────────────
# Each builder is a function — timestamps are generated when the function is called,
# not when the module is imported. This ensures dynamic, up-to-date timestamps.

def _payment_db_failure() -> dict:
    ts, t = _now(), _time()
    return {
        "alert_name":    "payment-service-db-failure",
        "service":       "payment-service",
        "environment":   "production",
        "error":         "HTTP 500 Internal Server Error",
        "error_message": "Failed to process payment request: database connection refused",
        "logs": [
            f"{ts} ERROR payment-service  Payment request failed: connection refused to postgres:5432",
            f"{ts} ERROR postgres          database restarting unexpectedly",
            f"{ts} ERROR postgres          database recovery in progress",
        ],
        "timeline": [
            f"{t} payment-service healthy",
            f"{t} PostgreSQL restarted",
            f"{t} PostgreSQL recovery started",
            f"{t} payment-service returned HTTP 500",
        ],
        "request": _REQUEST,
    }


def _auth_upstream_timeout() -> dict:
    ts, t = _now(), _time()
    return {
        "alert_name":    "auth-service-upstream-timeout",
        "service":       "auth-service",
        "environment":   "production",
        "error":         "503 Service Unavailable",
        "error_message": "Upstream timeout: identity-provider did not respond within 30s",
        "logs": [
            f"{ts} ERROR auth-service       upstream call to identity-provider timed out after 30s",
            f"{ts} WARN  identity-provider  high CPU detected — response degraded",
            f"{ts} ERROR auth-service       circuit breaker opened",
        ],
        "timeline": [
            f"{t} auth-service healthy",
            f"{t} identity-provider latency spike (>5s)",
            f"{t} auth-service upstream timeout (30s)",
            f"{t} circuit breaker opened",
            f"{t} 503 returned to all clients",
        ],
        "request": _REQUEST,
    }


def _api_gateway_500() -> dict:
    ts, t = _now(), _time()
    return {
        "alert_name":    "api-gateway-http-500",
        "service":       "api-gateway",
        "environment":   "production",
        "error":         "HTTP 500 Internal Server Error",
        "error_message": "Unhandled exception in request pipeline: NullPointerException",
        "logs": [
            f"{ts} ERROR api-gateway   NullPointerException in middleware chain",
            f"{ts} ERROR api-gateway   Failed to deserialize response from user-service",
            f"{ts} WARN  user-service  Schema version mismatch: expected v2, got v1",
        ],
        "timeline": [
            f"{t} api-gateway deployed (new version)",
            f"{t} user-service schema unchanged",
            f"{t} first 500 error reported",
            f"{t} error rate reached 100%",
        ],
        "request": _REQUEST,
    }


def _k8s_pod_oomkilled() -> dict:
    ts, t = _now(), _time()
    return {
        "alert_name":    "k8s-data-processor-oomkilled",
        "service":       "data-processor",
        "environment":   "production",
        "error":         "OOMKilled",
        "error_message": "Container exceeded memory limit and was killed by the OOM killer",
        "logs": [
            f"{ts} WARN  kubelet         Pod data-processor memory usage at 95% of limit",
            f"{ts} ERROR kubelet         OOMKilling container: memory cgroup out of memory",
            f"{ts} INFO  kubelet         Pod data-processor restarted (restartCount: 5)",
        ],
        "timeline": [
            f"{t} data-processor healthy",
            f"{t} memory usage exceeded 80%",
            f"{t} memory usage exceeded 95%",
            f"{t} OOMKilled — pod restarted",
        ],
        "request": _REQUEST,
    }


def _disk_full() -> dict:
    ts, t = _now(), _time()
    return {
        "alert_name":    "disk-full-log-aggregator",
        "service":       "log-aggregator",
        "environment":   "production",
        "error":         "No space left on device",
        "error_message": "Write failed: disk partition /var/log at 100% capacity",
        "logs": [
            f"{ts} WARN  log-aggregator  disk usage at 98% — 1 minute ago",
            f"{ts} ERROR log-aggregator  write: no space left on device (/var/log)",
            f"{ts} ERROR postgres        could not write to WAL: no space left on device",
        ],
        "timeline": [
            f"{t} disk at 90%",
            f"{t} disk at 98%",
            f"{t} disk at 100%",
            f"{t} log-aggregator write errors begin",
            f"{t} postgres WAL write failed",
        ],
        "request": _REQUEST,
    }


def _redis_connection_refused() -> dict:
    ts, t = _now(), _time()
    return {
        "alert_name":    "cache-service-redis-refused",
        "service":       "cache-service",
        "environment":   "production",
        "error":         "Connection Refused",
        "error_message": "Redis connection refused: ECONNREFUSED 127.0.0.1:6379",
        "logs": [
            f"{ts} ERROR cache-service   Redis connection refused: ECONNREFUSED 127.0.0.1:6379",
            f"{ts} ERROR redis           MISCONF Redis is configured to save RDB snapshots",
            f"{ts} WARN  redis           Can't save in background: fork: Cannot allocate memory",
        ],
        "timeline": [
            f"{t} redis healthy",
            f"{t} redis failed to fork for RDB snapshot",
            f"{t} redis stopped accepting connections",
            f"{t} cache-service ECONNREFUSED",
        ],
        "request": _REQUEST,
    }


def _certificate_expired() -> dict:
    ts, t = _now(), _time()
    return {
        "alert_name":    "tls-certificate-expired",
        "service":       "api-gateway",
        "environment":   "production",
        "error":         "SSL Certificate Expired",
        "error_message": "TLS handshake failed: certificate has expired",
        "logs": [
            f"{ts} ERROR nginx          SSL: error:14094415:SSL routines: certificate expired",
            f"{ts} ERROR api-gateway    TLS handshake failed for upstream billing-service",
            f"{ts} WARN  cert-manager   Certificate billing-service-tls expires in -1 days",
        ],
        "timeline": [
            f"{t} cert-manager warning: expiry in 7 days (alert missed)",
            f"{t} certificate expired",
            f"{t} TLS handshake failures begin",
            f"{t} all requests to billing-service failing",
        ],
        "request": _REQUEST,
    }


# ── Registry ──────────────────────────────────────────────────────────────────

INCIDENT_REGISTRY: dict[str, dict] = {
    "1": {
        "key":         "payment-db-failure",
        "description": "Payment service — PostgreSQL connection refused (HTTP 500)",
        "builder":     _payment_db_failure,
    },
    "2": {
        "key":         "auth-timeout",
        "description": "Auth service — upstream identity-provider timeout (503)",
        "builder":     _auth_upstream_timeout,
    },
    "3": {
        "key":         "api-gateway-500",
        "description": "API Gateway — NullPointerException after schema mismatch",
        "builder":     _api_gateway_500,
    },
    "4": {
        "key":         "k8s-pod-oomkilled",
        "description": "Kubernetes — data-processor pod OOMKilled (memory limit)",
        "builder":     _k8s_pod_oomkilled,
    },
    "5": {
        "key":         "disk-full",
        "description": "Log aggregator — /var/log disk at 100% capacity",
        "builder":     _disk_full,
    },
    "6": {
        "key":         "redis-refused",
        "description": "Cache service — Redis connection refused (fork failed)",
        "builder":     _redis_connection_refused,
    },
    "7": {
        "key":         "cert-expired",
        "description": "API Gateway — TLS certificate expired for billing-service",
        "builder":     _certificate_expired,
    },
}


def build_incident(key_or_number: str) -> dict | None:
    """
    Build a fresh incident (dynamic timestamps = right now) for the given
    key number (e.g. '1') or key name (e.g. 'payment-db-failure').
    Returns None if the key is not found in the registry.
    """
    # By menu number
    if key_or_number in INCIDENT_REGISTRY:
        return INCIDENT_REGISTRY[key_or_number]["builder"]()

    # By key name
    for entry in INCIDENT_REGISTRY.values():
        if entry["key"] == key_or_number:
            return entry["builder"]()

    return None


def list_keys() -> list[dict]:
    """Return registry entries as a plain list (sorted by number)."""
    return [
        {"number": num, "key": e["key"], "description": e["description"]}
        for num, e in INCIDENT_REGISTRY.items()
    ]
