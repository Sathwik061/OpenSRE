"""
sentinel/core/state_store.py
============================
Thread-safe in-memory storage for active and completed RCA investigations.
"""

import threading
from typing import Dict, Any, Optional, List


class StateStore:
    """Thread-safe store for investigation outputs and statuses."""

    def __init__(self):
        self._results: Dict[str, Any] = {}
        self._status: Dict[str, str] = {}
        self._lock = threading.Lock()

    def set_status(self, inv_id: str, status: str) -> None:
        with self._lock:
            self._status[inv_id] = status

    def get_status(self, inv_id: str) -> Optional[str]:
        with self._lock:
            return self._status.get(inv_id)

    def set_result(self, inv_id: str, result: Dict[str, Any], additional_keys: Optional[List[str]] = None) -> None:
        with self._lock:
            self._results[inv_id] = result
            self._status[inv_id] = "done"
            if additional_keys:
                for k in additional_keys:
                    if k:
                        self._results[str(k)] = result
                        self._status[str(k)] = "done"

    def get_result(self, inv_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if inv_id in self._results:
                return self._results[inv_id]

            # Search by instance_key or incident_key in records
            for v in self._results.values():
                if isinstance(v, dict):
                    if (
                        str(v.get("instance_key", "")) == inv_id
                        or str(v.get("incident_key", "")) == inv_id
                        or str(v.get("processInstanceKey", "")) == inv_id
                        or str(v.get("incidentKey", "")) == inv_id
                    ):
                        return v
            return None

    def list_all(self) -> List[Dict[str, str]]:
        with self._lock:
            return [
                {"id": inv_id, "status": self._status.get(inv_id, "unknown")}
                for inv_id in self._status
            ]


# Singleton instance
store = StateStore()
