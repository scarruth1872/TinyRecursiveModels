
import os
import json
import time
import asyncio
import requests
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger("OpenClawGateway")

# Configuration
SWARM_API_URL = "http://127.0.0.1:8001"
INBOX_FILE = "swarm_v2_artifacts/openclaw_inbox.json"
HEARTBEAT_FILE = "HEARTBEAT.md"


# --- Intent Classification ---

INTENT_ROUTING = {
    "code_task":      {"specialist": "Lead Developer", "keywords": [
        "implement", "build", "create", "write code", "fix bug", "refactor",
        "add feature", "generate", "scaffold", "deploy"
    ]},
    "question":       {"specialist": "Reasoning Engine", "keywords": [
        "explain", "why", "how does", "what is", "compare", "difference",
        "analyze", "understand", "reason"
    ]},
    "review":         {"specialist": "Security Auditor", "keywords": [
        "review", "audit", "check", "security", "vulnerability", "scan",
        "validate", "verify", "test"
    ]},
    "system_command": {"specialist": "Architect", "keywords": [
        "status", "restart", "configure", "setup", "monitor", "health",
        "deploy", "scale", "shutdown"
    ]},
    "research":       {"specialist": "Researcher", "keywords": [
        "research", "investigate", "explore", "find", "search", "discover",
        "latest", "benchmark", "compare frameworks"
    ]},
    "monitoring":     {"specialist": "Architect", "keywords": [
        "dashboard", "metrics", "report", "performance", "logs", "alerts"
    ]},
}


@dataclass
class InboundMessage:
    """Normalized message format from any channel."""
    text: str
    sender: str
    channel: str
    channel_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    intent: str = "unknown"
    target_specialist: str = "Architect"
    metadata: Dict[str, Any] = field(default_factory=dict)


# --- Channel Adapters ---

class ChannelAdapter(ABC):
    """Base class for channel adapters."""
    channel_name: str = "unknown"

    @abstractmethod
    async def poll(self) -> List[Dict[str, Any]]:
        """Poll for new messages. Returns list of raw messages."""
        ...

    @abstractmethod
    async def send(self, recipient: str, text: str) -> bool:
        """Send a message back to the channel."""
        ...

    def normalize(self, raw_msg: Dict[str, Any]) -> InboundMessage:
        """Convert raw channel message to InboundMessage."""
        return InboundMessage(
            text=raw_msg.get("text", ""),
            sender=raw_msg.get("sender", "unknown"),
            channel=self.channel_name,
            channel_id=raw_msg.get("channel_id", ""),
            metadata=raw_msg,
        )


class LocalFileAdapter(ChannelAdapter):
    """Reads messages from a local JSON file (existing behavior)."""
    channel_name = "local_file"

    def __init__(self, inbox_path: str = INBOX_FILE):
        self.inbox_path = inbox_path

    async def poll(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.inbox_path):
            return []
        try:
            with open(self.inbox_path, "r") as f:
                messages = json.load(f)
            if messages:
                with open(self.inbox_path, "w") as f:
                    json.dump([], f)
            return messages
        except Exception:
            return []

    async def send(self, recipient: str, text: str) -> bool:
        logger.info(f"[LocalFile] Response to {recipient}: {text[:100]}...")
        return True


class TelegramAdapter(ChannelAdapter):
    """Telegram Bot API adapter (scaffold — needs TELEGRAM_BOT_TOKEN)."""
    channel_name = "telegram"

    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.last_update_id = 0

    async def poll(self) -> List[Dict[str, Any]]:
        if not self.token:
            return []
        # Scaffold: would call https://api.telegram.org/bot{token}/getUpdates
        logger.debug("[Telegram] Poll — no token configured")
        return []

    async def send(self, recipient: str, text: str) -> bool:
        if not self.token:
            return False
        # Scaffold: would call https://api.telegram.org/bot{token}/sendMessage
        return False


class DiscordAdapter(ChannelAdapter):
    """Discord adapter (scaffold — needs DISCORD_BOT_TOKEN)."""
    channel_name = "discord"

    def __init__(self):
        self.token = os.getenv("DISCORD_BOT_TOKEN", "")

    async def poll(self) -> List[Dict[str, Any]]:
        if not self.token:
            return []
        logger.debug("[Discord] Poll — no token configured")
        return []

    async def send(self, recipient: str, text: str) -> bool:
        return False


# --- Gateway ---

class OpenClawGateway:
    """
    OpenClaw Gateway (Perception Layer).
    Multi-channel interface with intent classification that routes to Swarm OS.
    """
    def __init__(self):
        os.makedirs(os.path.dirname(INBOX_FILE), exist_ok=True)
        if not os.path.exists(INBOX_FILE):
             with open(INBOX_FILE, "w") as f:
                 json.dump([], f)

        # Initialize channel adapters
        self.adapters: List[ChannelAdapter] = [
            LocalFileAdapter(),
            TelegramAdapter(),
            DiscordAdapter(),
        ]

        self._stats = {
            "messages_processed": 0,
            "intents": {},
        }

    def classify_intent(self, text: str) -> tuple:
        """
        Classify inbound message intent using keyword matching.

        Returns:
            (intent_name, target_specialist)
        """
        text_lower = text.lower()
        best_intent = "system_command"
        best_score = 0

        for intent_name, config in INTENT_ROUTING.items():
            score = sum(1 for kw in config["keywords"] if kw in text_lower)
            if score > best_score:
                best_score = score
                best_intent = intent_name

        specialist = INTENT_ROUTING[best_intent]["specialist"]
        return best_intent, specialist

    async def start(self):
        logger.info("[OpenClaw] Gateway Active. Monitoring multi-channel signals...")
        while True:
            try:
                # Poll all channel adapters
                for adapter in self.adapters:
                    raw_messages = await adapter.poll()
                    for raw_msg in raw_messages:
                        msg = adapter.normalize(raw_msg)
                        # Classify intent
                        msg.intent, msg.target_specialist = self.classify_intent(msg.text)
                        logger.info(f"[OpenClaw] {msg.channel}/{msg.sender}: "
                                    f"intent={msg.intent} → {msg.target_specialist}")
                        await self.route_to_swarm(msg)

                await self.check_proactive_triggers()
            except Exception as e:
                logger.error(f"[OpenClaw] Error in gateway loop: {e}")
            await asyncio.sleep(5)

    async def route_to_swarm(self, msg: InboundMessage):
        """Route a classified message to the appropriate specialist."""
        try:
            payload = {
                "task": msg.text,
                "required_specialty": msg.target_specialist
            }
            resp = requests.post(f"{SWARM_API_URL}/mesh/route", json=payload)
            if resp.status_code == 200:
                logger.info(f"[OpenClaw] Routed to {msg.target_specialist}. "
                            f"Response: {resp.json().get('response', '')[:100]}...")
            else:
                logger.warning(f"[OpenClaw] Failed to route: {resp.status_code}")
        except Exception as e:
            logger.warning(f"[OpenClaw] Routing error: {e}")

        self._stats["messages_processed"] += 1
        self._stats["intents"][msg.intent] = self._stats["intents"].get(msg.intent, 0) + 1

    async def check_proactive_triggers(self):
        """Proactive check that might add a task to HEARTBEAT.md."""
        if os.path.exists(HEARTBEAT_FILE):
            with open(HEARTBEAT_FILE, "r") as f:
                content = f.read()

            import random
            if "- [ ]" not in content and random.random() < 0.05:
                logger.info("[OpenClaw] Proactive trigger: Requesting system resonance check.")
                new_task = f"\n- [ ] Perform a system-wide resonance check and report harmony status."
                if "## neural_checkpoints" in content:
                    content = content.replace("## neural_checkpoints", f"{new_task}\n\n## neural_checkpoints")
                else:
                    content += new_task

                with open(HEARTBEAT_FILE, "w") as f:
                    f.write(content)

    def get_stats(self) -> Dict[str, Any]:
        """Get gateway statistics."""
        return {
            "channels": [a.channel_name for a in self.adapters],
            "active_channels": [a.channel_name for a in self.adapters
                                if not (hasattr(a, 'token') and not a.token)],
            **self._stats,
        }


if __name__ == "__main__":
    gateway = OpenClawGateway()
    asyncio.run(gateway.start())
