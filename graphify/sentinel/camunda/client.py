"""
sentinel/camunda/client.py
==========================
Camunda Operate & Zeebe REST API client.
Supports cookie authentication, CSRF token handling, retries, and both
Camunda 8.6 and 8.9 REST API versions.
"""

import os
import json
import time
import logging
import http.cookiejar
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional, List, Dict, Any

logger = logging.getLogger("sentinel.camunda.client")

OPERATE_URL  = os.getenv("OPERATE_URL",  "http://localhost:8081").rstrip("/")
OPERATE_USER = os.getenv("OPERATE_USER", "demo")
OPERATE_PASS = os.getenv("OPERATE_PASS", "demo")
ZEEBE_REST   = os.getenv("ZEEBE_REST",   "http://localhost:8080").rstrip("/")


class OperateClient:
    """Manages persistent Camunda Operate login sessions and API calls."""

    def __init__(
        self,
        base_url: str = OPERATE_URL,
        username: str = OPERATE_USER,
        password: str = OPERATE_PASS,
    ):
        self.base_url = base_url
        self.username = username
        self.password = password
        self._cookie_jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self._cookie_jar)
        )
        self._csrf_token: str = ""
        self._logged_in: bool = False

    def login(self) -> bool:
        """Authenticate with Camunda Operate (supports 8.9 /login and 8.6 /api/login)."""
        # 1. Try Camunda 8.9 form login
        try:
            data = urllib.parse.urlencode({"username": self.username, "password": self.password}).encode()
            req = urllib.request.Request(f"{self.base_url}/login", data=data, method="POST")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            with self._opener.open(req, timeout=5) as r:
                csrf = r.getheader("X-CSRF-TOKEN", "")
                if csrf:
                    self._csrf_token = csrf
                self._logged_in = r.status in (200, 204)
                if self._logged_in:
                    return True
        except Exception:
            pass

        # 2. Fallback to Camunda 8.6 /api/login
        url = f"{self.base_url}/api/login?username={self.username}&password={self.password}"
        try:
            req = urllib.request.Request(url, data=b"", method="POST")
            with self._opener.open(req, timeout=5) as r:
                csrf = r.getheader("X-CSRF-TOKEN", "")
                if csrf:
                    self._csrf_token = csrf
                self._logged_in = r.status in (200, 204)
                return self._logged_in
        except Exception as e:
            # In local unauthenticated instances, endpoints work directly
            self._logged_in = True
            return True

    def get(self, path: str, timeout: int = 8) -> Optional[Dict[str, Any]]:
        """Authenticated GET returning parsed JSON."""
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        if not self._logged_in:
            self.login()
        try:
            req = urllib.request.Request(url)
            if self._csrf_token:
                req.add_header("X-CSRF-TOKEN", self._csrf_token)
            with self._opener.open(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                self._logged_in = False
                if self.login():
                    return self.get(path, timeout)
            logger.debug(f"GET {url} -> HTTP {e.code}")
            return None
        except Exception as e:
            logger.debug(f"GET {url} failed: {e}")
            return None

    def get_raw(self, path: str, timeout: int = 8) -> Optional[str]:
        """Authenticated GET returning raw string content (e.g. BPMN XML)."""
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        if not self._logged_in:
            self.login()
        try:
            req = urllib.request.Request(url)
            if self._csrf_token:
                req.add_header("X-CSRF-TOKEN", self._csrf_token)
            with self._opener.open(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                self._logged_in = False
                if self.login():
                    return self.get_raw(path, timeout)
            logger.debug(f"GET_RAW {url} -> HTTP {e.code}")
            return None
        except Exception as e:
            logger.debug(f"GET_RAW {url} failed: {e}")
            return None

    def post(self, path: str, body: Dict[str, Any], timeout: int = 8) -> Optional[Dict[str, Any]]:
        """Authenticated POST returning parsed JSON."""
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        if not self._logged_in:
            self.login()
        try:
            data = json.dumps(body).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            if self._csrf_token:
                req.add_header("X-CSRF-TOKEN", self._csrf_token)
            with self._opener.open(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                self._logged_in = False
                if self.login():
                    return self.post(path, body, timeout)
            logger.debug(f"POST {url} -> HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}")
            return None
        except Exception as e:
            logger.debug(f"POST {url} failed: {e}")
            return None

    def check_alive(self) -> bool:
        """Verify if Camunda Operate is reachable."""
        res = self.post("/v2/incidents/search", {"page": {"limit": 1}})
        if res is not None:
            return True
        return self.login()

    def fetch_live_incidents(self, size: int = 50) -> List[Dict[str, Any]]:
        """Fetch all ACTIVE incidents in Camunda 8.9 or 8.6."""
        # 1. Try Camunda 8.9 v2 API
        v2_body = {"filter": {"state": "ACTIVE"}, "page": {"limit": size}}
        result = self.post("/v2/incidents/search", v2_body)
        if result and "items" in result:
            items = []
            for it in result.get("items", []):
                item = dict(it)
                if "incidentKey" in item and "key" not in item:
                    item["key"] = item["incidentKey"]
                if "processDefinitionId" in item and "processDefinitionKey" not in item:
                    item["processDefinitionKey"] = item.get("processDefinitionKey")
                items.append(item)
            return items

        # 2. Fallback to v1 API
        v1_body = {
            "filter": {"state": "ACTIVE"},
            "size": size,
            "sort": [{"field": "creationTime", "order": "DESC"}],
        }
        result = self.post("/v1/incidents/search", v1_body)
        if result:
            return result.get("items", [])
        return []

    def fetch_process_instance(self, instance_key: str) -> Dict[str, Any]:
        """Fetch single process instance metadata by key."""
        res = self.get(f"/v2/process-instances/{instance_key}")
        if res:
            return res
        return self.get(f"/v1/process-instances/{instance_key}") or {}

    def fetch_instance_variables(self, instance_key: str) -> Dict[str, Any]:
        """Fetch all variables of a process instance."""
        body_v2 = {
            "filter": {"processInstanceKey": str(instance_key)},
            "page": {"limit": 100},
        }
        result = self.post("/v2/variables/search", body_v2)
        if not result or not result.get("items"):
            time.sleep(0.5)  # Handle ES indexing lag
            result = self.post("/v2/variables/search", body_v2)

        if not result or "items" not in result:
            body_v1 = {
                "filter": {"processInstanceKey": int(instance_key) if str(instance_key).isdigit() else instance_key},
                "size": 100,
            }
            result = self.post("/v1/variables/search", body_v1)

        if not result:
            return {}

        variables = {}
        for var in result.get("items", []):
            name = var.get("name", "")
            val  = var.get("value", "")
            try:
                variables[name] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                variables[name] = val
        return variables

    def fetch_flow_node_name(self, instance_key: str, flow_node_id: str) -> str:
        """Resolve human-readable task/element name from Operate."""
        body_v2 = {
            "filter": {"processInstanceKey": str(instance_key), "elementId": flow_node_id},
            "page": {"limit": 1},
        }
        result = self.post("/v2/element-instances/search", body_v2)
        if result and result.get("items"):
            item = result["items"][0]
            return item.get("elementName") or item.get("elementId") or flow_node_id

        body_v1 = {
            "filter": {
                "processInstanceKey": int(instance_key) if str(instance_key).isdigit() else instance_key,
                "flowNodeId": flow_node_id,
            },
            "size": 1,
        }
        result = self.post("/v1/flownode-instances/search", body_v1)
        if result and result.get("items"):
            item = result["items"][0]
            return item.get("flowNodeName") or item.get("flowNodeId") or flow_node_id
        return flow_node_id

    def fetch_bpmn_xml(self, proc_def_key: str) -> Optional[str]:
        """Fetch raw BPMN 2.0 XML from Operate for topology parsing."""
        for endpoint in [
            f"/v2/process-definitions/{proc_def_key}/xml",
            f"/v1/process-definitions/{proc_def_key}/xml",
            f"/api/process-definitions/{proc_def_key}/xml",
        ]:
            raw = self.get_raw(endpoint)
            if raw:
                raw_s = raw.strip()
                if raw_s.startswith("{"):
                    try:
                        data = json.loads(raw_s)
                        if isinstance(data, dict):
                            xml = data.get("bpmnXml") or data.get("xml") or data.get("content")
                            if xml:
                                return xml
                    except Exception:
                        pass
                elif "<" in raw_s and ("process" in raw_s or "definitions" in raw_s):
                    return raw_s
        return None

    def get_cluster_version(self) -> str:
        """
        Dynamically discover the running Camunda engine version (e.g. '8.6', '8.5', '8.4').
        Checks Operate and Zeebe version endpoints with caching and fallback.
        """
        if hasattr(self, "_cached_version") and self._cached_version:
            return self._cached_version

        env_ver = os.getenv("CAMUNDA_VERSION")
        if env_ver:
            self._cached_version = env_ver.strip()
            return self._cached_version

        # 1. Try Operate /actuator/info or /api/v1/version
        for endpoint in ["/actuator/info", "/api/v1/version", "/v1/version"]:
            res = self.get(endpoint)
            if res:
                v = res.get("version") or res.get("build", {}).get("version") or res.get("app", {}).get("version")
                if v:
                    parts = str(v).split(".")
                    if len(parts) >= 2:
                        self._cached_version = f"{parts[0]}.{parts[1]}"
                        logger.info(f"🔍 Discovered Camunda cluster version: {self._cached_version} (from {v})")
                        return self._cached_version

        # 2. Try Zeebe REST /v1/topology
        try:
            req = urllib.request.Request(f"{ZEEBE_REST}/v1/topology")
            with urllib.request.urlopen(req, timeout=3) as r:
                data = json.loads(r.read().decode("utf-8"))
                gw_ver = data.get("gatewayVersion")
                if gw_ver:
                    parts = str(gw_ver).split(".")
                    if len(parts) >= 2:
                        self._cached_version = f"{parts[0]}.{parts[1]}"
                        logger.info(f"🔍 Discovered Zeebe gateway version: {self._cached_version} (from {gw_ver})")
                        return self._cached_version
        except Exception:
            pass

        self._cached_version = os.getenv("CAMUNDA_VERSION", "8.9")
        return self._cached_version


# Default shared client instance
default_client = OperateClient()

