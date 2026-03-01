"""
Secrets Vault — Encrypted Credential Management
Replaces hardcoded keys with Fernet-encrypted storage.
Falls back to base64 obfuscation if cryptography is unavailable.
"""

import os
import json
import base64
import logging
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger("SecretsVault")

VAULT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", ".swarm"
)
VAULT_FILE = os.path.join(VAULT_DIR, "secrets.vault")
KEY_FILE = os.path.join(VAULT_DIR, ".vault_key")

# Check if Fernet is available
try:
    from cryptography.fernet import Fernet
    HAS_FERNET = True
except ImportError:
    HAS_FERNET = False
    logger.debug("[SecretsVault] cryptography not installed — using base64 fallback")


class SecretsVault:
    """
    Encrypted secrets storage with Fernet (or base64 fallback).

    Secrets are stored in `.swarm/secrets.vault` (should be gitignored).
    Master key is auto-generated on first use and stored in `.swarm/.vault_key`.
    """

    def __init__(self, vault_path: str = VAULT_FILE, key_path: str = KEY_FILE):
        self.vault_path = os.path.abspath(vault_path)
        self.key_path = os.path.abspath(key_path)
        os.makedirs(os.path.dirname(self.vault_path), exist_ok=True)

        # Ensure .swarm is in .gitignore
        self._ensure_gitignore()

        self._master_key = self._load_or_create_key()
        self._secrets: Dict[str, str] = self._load_vault()

    def _ensure_gitignore(self):
        """Add .swarm/ to .gitignore if not present."""
        gitignore = os.path.join(os.path.dirname(self.vault_path), "..", ".gitignore")
        gitignore = os.path.abspath(gitignore)
        if os.path.exists(gitignore):
            with open(gitignore, "r", encoding="utf-8") as f:
                content = f.read()
            if ".swarm/" not in content:
                with open(gitignore, "a", encoding="utf-8") as f:
                    f.write("\n# Secrets vault\n.swarm/\n")

    def _load_or_create_key(self) -> bytes:
        """Load master key from disk or generate a new one."""
        if os.path.exists(self.key_path):
            with open(self.key_path, "rb") as f:
                return f.read()

        if HAS_FERNET:
            key = Fernet.generate_key()
        else:
            # Fallback: random 32-byte key, base64 encoded
            key = base64.urlsafe_b64encode(os.urandom(32))

        with open(self.key_path, "wb") as f:
            f.write(key)

        logger.info("[SecretsVault] Generated new master key")
        return key

    def _encrypt(self, plaintext: str) -> str:
        """Encrypt a string value."""
        if HAS_FERNET:
            f = Fernet(self._master_key)
            return f.encrypt(plaintext.encode()).decode()
        else:
            # Base64 obfuscation fallback (NOT secure, better than plaintext)
            combined = plaintext.encode()
            return base64.urlsafe_b64encode(combined).decode()

    def _decrypt(self, ciphertext: str) -> str:
        """Decrypt a string value."""
        if HAS_FERNET:
            f = Fernet(self._master_key)
            return f.decrypt(ciphertext.encode()).decode()
        else:
            return base64.urlsafe_b64decode(ciphertext.encode()).decode()

    def _load_vault(self) -> Dict[str, str]:
        """Load encrypted vault from disk."""
        if not os.path.exists(self.vault_path):
            return {}
        try:
            with open(self.vault_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_vault(self):
        """Save vault to disk."""
        with open(self.vault_path, "w", encoding="utf-8") as f:
            json.dump(self._secrets, f, indent=2)

    def set_secret(self, key: str, value: str):
        """Store an encrypted secret."""
        self._secrets[key] = self._encrypt(value)
        self._save_vault()
        logger.info(f"[SecretsVault] Stored secret: {key}")

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve and decrypt a secret."""
        encrypted = self._secrets.get(key)
        if encrypted is None:
            return None
        try:
            return self._decrypt(encrypted)
        except Exception as e:
            logger.error(f"[SecretsVault] Decryption failed for {key}: {e}")
            return None

    def delete_secret(self, key: str) -> bool:
        """Delete a secret."""
        if key in self._secrets:
            del self._secrets[key]
            self._save_vault()
            return True
        return False

    def list_keys(self) -> List[str]:
        """List stored secret key names (not values)."""
        return list(self._secrets.keys())

    def rotate_key(self):
        """
        Rotate the master encryption key.
        Re-encrypts all secrets with a new key.
        """
        # Decrypt all values with old key
        plaintext = {}
        for key in self._secrets:
            val = self.get_secret(key)
            if val is not None:
                plaintext[key] = val

        # Generate new key
        if HAS_FERNET:
            self._master_key = Fernet.generate_key()
        else:
            self._master_key = base64.urlsafe_b64encode(os.urandom(32))

        with open(self.key_path, "wb") as f:
            f.write(self._master_key)

        # Re-encrypt all values
        self._secrets = {}
        for key, value in plaintext.items():
            self._secrets[key] = self._encrypt(value)
        self._save_vault()

        logger.info(f"[SecretsVault] Key rotated. Re-encrypted {len(plaintext)} secrets.")

    def get_stats(self) -> Dict:
        return {
            "total_secrets": len(self._secrets),
            "encryption": "fernet" if HAS_FERNET else "base64_fallback",
            "vault_path": self.vault_path,
        }


# Singleton
_vault: Optional[SecretsVault] = None

def get_secrets_vault() -> SecretsVault:
    global _vault
    if _vault is None:
        _vault = SecretsVault()
    return _vault
