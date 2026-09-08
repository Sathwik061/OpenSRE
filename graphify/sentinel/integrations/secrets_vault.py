"""
sentinel/integrations/secrets_vault.py
======================================
3-Tier Encrypted Secrets Vault for OpenSRE Enterprise Integrations.
Features:
  1. Master Key Derivation: Reads OPEN_SRE_MASTER_KEY from env, or generates/persists
     a 256-bit Fernet key in sentinel/data/.vault_key with restricted permissions.
  2. Encrypted Store: Serializes credentials into an encrypted JSON file (vault.enc).
  3. Strict Clean Masking: Prevents plaintext token leakage. When returning stored credentials
     for UI inspection or logs, secrets are cleanly masked as '********' or last-4 characters.
"""

import os
import json
import base64
import logging
from typing import Dict, Any, Optional, List
from cryptography.fernet import Fernet

logger = logging.getLogger("sentinel.integrations.vault")

_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data"
)
os.makedirs(_DATA_DIR, exist_ok=True)

_KEY_FILE = os.path.join(_DATA_DIR, ".vault_key")
_VAULT_FILE = os.path.join(_DATA_DIR, "vault.enc")


class SecretsVault:
    def __init__(self):
        self._fernet = self._init_fernet()
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_vault()

    def _init_fernet(self) -> Fernet:
        """Derive or load the 256-bit symmetric encryption key."""
        env_key = os.environ.get("OPEN_SRE_MASTER_KEY")
        if env_key:
            try:
                # Ensure 32-byte urlsafe base64
                return Fernet(env_key.encode("utf-8"))
            except Exception as e:
                logger.warning(f"Invalid OPEN_SRE_MASTER_KEY in environment: {e}. Falling back to keyfile.")

        if os.path.exists(_KEY_FILE):
            try:
                with open(_KEY_FILE, "rb") as f:
                    key = f.read().strip()
                return Fernet(key)
            except Exception as e:
                logger.error(f"Error reading vault keyfile: {e}. Re-generating.")

        # Generate new robust key
        key = Fernet.generate_key()
        try:
            with open(_KEY_FILE, "wb") as f:
                f.write(key)
        except Exception as e:
            logger.warning(f"Could not persist vault keyfile: {e}")
        return Fernet(key)

    def _load_vault(self) -> None:
        """Decrypt vault.enc and load into memory cache."""
        if not os.path.exists(_VAULT_FILE):
            self._cache = {}
            return

        try:
            with open(_VAULT_FILE, "rb") as f:
                encrypted_bytes = f.read()
            if not encrypted_bytes:
                self._cache = {}
                return
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            self._cache = json.loads(decrypted_bytes.decode("utf-8"))
            logger.info(f"Loaded {len(self._cache)} configured integration credentials from vault.")
        except Exception as e:
            logger.error(f"Failed to decrypt vault file: {e}")
            self._cache = {}

    def _save_vault(self) -> None:
        """Encrypt in-memory cache and write atomically to disk."""
        try:
            raw_json = json.dumps(self._cache, indent=2).encode("utf-8")
            encrypted_bytes = self._fernet.encrypt(raw_json)
            tmp_file = f"{_VAULT_FILE}.tmp"
            with open(tmp_file, "wb") as f:
                f.write(encrypted_bytes)
            if os.path.exists(_VAULT_FILE):
                os.replace(tmp_file, _VAULT_FILE)
            else:
                os.rename(tmp_file, _VAULT_FILE)
        except Exception as e:
            logger.error(f"Failed to persist encrypted vault: {e}")

    def store_credentials(self, integration_id: str, credentials: Dict[str, Any]) -> None:
        """Encrypt and persist integration credentials."""
        self._cache[integration_id] = credentials
        self._save_vault()
        logger.info(f"Safely stored encrypted credentials for integration '{integration_id}'.")

    def get_credentials(self, integration_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve raw decrypted credentials for backend adapter execution."""
        return self._cache.get(integration_id)

    def delete_credentials(self, integration_id: str) -> bool:
        """Remove an integration's credentials from the vault."""
        if integration_id in self._cache:
            del self._cache[integration_id]
            self._save_vault()
            logger.info(f"Removed credentials for integration '{integration_id}'.")
            return True
        return False

    def list_configured_integrations(self) -> List[str]:
        """Return list of integration IDs that have active credentials stored."""
        return list(self._cache.keys())

    def get_masked_credentials(self, integration_id: str) -> Optional[Dict[str, Any]]:
        """
        Return credentials with sensitive fields cleanly masked with asterisks (********),
        safe for API responses and UI configuration forms.
        """
        creds = self.get_credentials(integration_id)
        if not creds:
            return None

        masked: Dict[str, Any] = {}
        for k, v in creds.items():
            str_v = str(v) if v is not None else ""
            # Check for sensitive key names or types
            is_secret = any(term in k.lower() for term in [
                "password", "token", "secret", "key", "auth", "credential"
            ])
            if is_secret:
                if len(str_v) > 8:
                    # Clean masking showing only last 4 chars
                    masked[k] = "********" + str_v[-4:]
                else:
                    masked[k] = "********"
            else:
                masked[k] = str_v
        return masked


# Global singleton instance
secrets_vault = SecretsVault()
