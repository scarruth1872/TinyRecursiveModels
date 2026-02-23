"""
Mutual Agent Trust (MAT) Protocol - Phase 5
Standardized communication and cryptographic trust for autonomous agent loops.
"""

import hmac
import hashlib
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("MAT")
SECRET_KEY = "swarm_v5_autonomy_alpha_secret"

def generate_trust_token(sender_role: str, target_role: str, task_id: str) -> str:
    """
    Generate a task-scoped, time-windowed HMAC token for secure agent-to-agent messaging.
    Default window: 300 seconds (5 minutes).
    """
    window = int(time.time() / 300)
    payload = f"{sender_role}->{target_role}:{task_id}:{window}"
    return hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()

def verify_trust_token(sender_role: str, target_role: str, task_id: str, token: str) -> bool:
    """
    Verify an incoming agent message against the current or previous time window.
    """
    current_window = int(time.time() / 300)
    # Check two windows to avoid race conditions at window boundaries
    for window in [current_window, current_window - 1]:
        payload = f"{sender_role}->{target_role}:{task_id}:{window}"
        expected = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(expected, token):
            return True
            
    logger.warning(f"TRUST FAILURE: Unauthorized message from {sender_role} to {target_role} (Task: {task_id})")
    return False

class AgentHandshake:
    """Helper class for managing agent-to-agent handshakes."""
    
    @staticmethod
    def create_secure_payload(sender_role: str, target_role: str, task_id: str, data: Any) -> Dict[str, Any]:
        token = generate_trust_token(sender_role, target_role, task_id)
        return {
            "header": {
                "sender": sender_role,
                "target": target_role,
                "task_id": task_id,
                "trust_token": token,
                "protocol": "MAT/1.0"
            },
            "content": data
        }

    @staticmethod
    def validate_secure_payload(payload: Dict[str, Any]) -> bool:
        header = payload.get("header", {})
        return verify_trust_token(
            header.get("sender"),
            header.get("target"),
            header.get("task_id"),
            header.get("trust_token")
        )
