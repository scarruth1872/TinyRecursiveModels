"""
Agent Mailbox — File-based Async Agent-to-Agent Messaging
Implements .swarm/mailboxes/{agent}/inbox.json for SEND_MESSAGE and BROADCAST
patterns as specified by the QIAE framework.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("AgentMailbox")

MAILBOX_ROOT = os.path.join(
    os.path.dirname(__file__), "..", "..", ".swarm", "mailboxes"
)

DEFAULT_TTL_MINUTES = 60


class AgentMailbox:
    """
    File-based async messaging between agents.

    Each agent has a mailbox at .swarm/mailboxes/{agent_id}/inbox.json.
    Messages have a TTL and auto-expire. Secured via MAT trust tokens.
    """

    def __init__(self, agent_id: str, mailbox_root: str = MAILBOX_ROOT):
        self.agent_id = agent_id
        self.mailbox_root = os.path.abspath(mailbox_root)
        self._inbox_path = os.path.join(self.mailbox_root, agent_id, "inbox.json")
        os.makedirs(os.path.dirname(self._inbox_path), exist_ok=True)

        # Ensure inbox exists
        if not os.path.exists(self._inbox_path):
            self._write(self._inbox_path, [])

    def send(self, target_agent: str, message: str,
             subject: str = "", priority: str = "normal",
             metadata: Dict = None) -> bool:
        """
        Send a message to another agent's inbox.

        Args:
            target_agent: Target agent ID
            message: Message body
            subject: Optional subject line
            priority: normal, high, urgent
            metadata: Additional metadata
        """
        target_path = os.path.join(self.mailbox_root, target_agent, "inbox.json")
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        msg = {
            "from": self.agent_id,
            "to": target_agent,
            "subject": subject,
            "message": message,
            "priority": priority,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(minutes=DEFAULT_TTL_MINUTES)).isoformat(),
            "read": False,
        }

        # Add trust token if available
        try:
            from swarm_v2.core.comm_protocol import AgentHandshake
            payload = AgentHandshake.create_secure_payload(
                self.agent_id, target_agent, f"mail-{msg['timestamp']}", message
            )
            msg["trust_token"] = payload["header"]["trust_token"]
        except ImportError:
            pass

        inbox = self._read(target_path)
        inbox.append(msg)
        self._write(target_path, inbox)

        logger.info(f"[Mailbox] {self.agent_id} → {target_agent}: {subject or message[:40]}")
        return True

    def broadcast(self, message: str, subject: str = "",
                  exclude: List[str] = None) -> int:
        """
        Broadcast a message to ALL registered agent mailboxes.

        Args:
            message: Message body
            subject: Subject line
            exclude: Agent IDs to exclude

        Returns:
            Number of agents messaged
        """
        exclude = set(exclude or [])
        exclude.add(self.agent_id)  # Don't send to self

        count = 0
        if os.path.exists(self.mailbox_root):
            for agent_dir in os.listdir(self.mailbox_root):
                if agent_dir not in exclude:
                    self.send(agent_dir, message, subject=subject, priority="normal")
                    count += 1

        logger.info(f"[Mailbox] {self.agent_id} broadcast to {count} agents: {subject or message[:40]}")
        return count

    def receive(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Read and consume pending messages from own inbox.
        Removes consumed messages and expired messages.

        Args:
            limit: Max messages to return

        Returns:
            List of messages
        """
        inbox = self._read(self._inbox_path)
        now = datetime.now()

        # Filter out expired messages
        valid = []
        for msg in inbox:
            expires = msg.get("expires_at", "")
            if expires:
                try:
                    exp_dt = datetime.fromisoformat(expires)
                    if exp_dt < now:
                        continue
                except (ValueError, TypeError):
                    pass
            valid.append(msg)

        # Take up to limit messages
        consumed = valid[:limit]
        remaining = valid[limit:]

        # Mark consumed as read
        for msg in consumed:
            msg["read"] = True

        # Write back remaining
        self._write(self._inbox_path, remaining)

        if consumed:
            logger.info(f"[Mailbox] {self.agent_id} received {len(consumed)} messages")

        return consumed

    def peek(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Read messages without consuming them."""
        inbox = self._read(self._inbox_path)
        now = datetime.now()

        # Filter expired
        valid = [
            msg for msg in inbox
            if not self._is_expired(msg, now)
        ]

        return valid[:limit]

    def count_pending(self) -> int:
        """Count unread pending messages."""
        inbox = self._read(self._inbox_path)
        now = datetime.now()
        return sum(1 for msg in inbox if not self._is_expired(msg, now))

    def clear(self):
        """Clear all messages in inbox."""
        self._write(self._inbox_path, [])

    def _is_expired(self, msg: Dict, now: datetime) -> bool:
        expires = msg.get("expires_at", "")
        if expires:
            try:
                return datetime.fromisoformat(expires) < now
            except (ValueError, TypeError):
                pass
        return False

    def _read(self, path: str) -> List[Dict]:
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write(self, path: str, data: List[Dict]):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def get_stats(self) -> Dict[str, Any]:
        inbox = self._read(self._inbox_path)
        return {
            "agent_id": self.agent_id,
            "pending_messages": len(inbox),
            "inbox_path": self._inbox_path,
        }

    @staticmethod
    def list_agents(mailbox_root: str = MAILBOX_ROOT) -> List[str]:
        """List all agents with mailboxes."""
        root = os.path.abspath(mailbox_root)
        if not os.path.exists(root):
            return []
        return [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
