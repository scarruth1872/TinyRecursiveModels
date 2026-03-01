"""
Kanban Board — Task State Machine & Agent Orchestration API
First-class Kanban board for agents managing agents.
Cards flow: TODO → IN_PROGRESS → REVIEW → DONE.
Moving to IN_PROGRESS auto-allocates worktree + port.
"""

import os
import json
import uuid
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("KanbanBoard")

KANBAN_STATE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "swarm_v2_artifacts", "kanban_state.json"
)


class CardStatus(Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


# Valid transitions
TRANSITIONS = {
    CardStatus.TODO: [CardStatus.IN_PROGRESS],
    CardStatus.IN_PROGRESS: [CardStatus.REVIEW, CardStatus.TODO],  # can return to TODO
    CardStatus.REVIEW: [CardStatus.DONE, CardStatus.IN_PROGRESS],  # can reject back
    CardStatus.DONE: [CardStatus.ARCHIVED],
    CardStatus.ARCHIVED: [],
}

PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


@dataclass
class KanbanCard:
    """A task card on the Kanban board."""
    card_id: str
    title: str
    description: str = ""
    status: str = "TODO"
    assignee: str = ""
    priority: str = "medium"
    tags: List[str] = field(default_factory=list)
    worktree_path: str = ""
    allocated_port: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    history: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card_id": self.card_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "assignee": self.assignee,
            "priority": self.priority,
            "tags": self.tags,
            "worktree_path": self.worktree_path,
            "allocated_port": self.allocated_port,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "history": self.history,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "KanbanCard":
        card = KanbanCard.__new__(KanbanCard)
        for k, v in d.items():
            setattr(card, k, v)
        return card


class KanbanBoard:
    """
    Kanban board data layer — task state machine with agent orchestration.

    Cards transition through TODO → IN_PROGRESS → REVIEW → DONE.
    Moving a card to IN_PROGRESS auto-triggers:
      - WorktreeManager.create_worktree() for Isolation 0
      - PortManager.acquire_port() for port allocation
    """

    def __init__(self, state_path: str = KANBAN_STATE_PATH):
        self.state_path = os.path.abspath(state_path)
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        self._cards: Dict[str, KanbanCard] = self._load()

    def _load(self) -> Dict[str, KanbanCard]:
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return {cid: KanbanCard.from_dict(d) for cid, d in data.items()}
            except Exception:
                return {}
        return {}

    def _save(self):
        data = {cid: card.to_dict() for cid, card in self._cards.items()}
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def create_card(self, title: str, description: str = "",
                    assignee: str = "", priority: str = "medium",
                    tags: List[str] = None) -> str:
        """
        Create a new task card in TODO column.

        Returns:
            card_id
        """
        card_id = f"card-{uuid.uuid4().hex[:8]}"
        card = KanbanCard(
            card_id=card_id,
            title=title,
            description=description,
            assignee=assignee,
            priority=priority,
            tags=tags or [],
        )
        card.history.append({
            "action": "created",
            "timestamp": card.created_at,
            "details": f"Card created: {title}",
        })

        self._cards[card_id] = card
        self._save()
        logger.info(f"[Kanban] Created card: {card_id} — {title}")
        return card_id

    def move_card(self, card_id: str, target_status: str) -> Dict[str, Any]:
        """
        Move a card to a new column. Validates transition.
        Auto-triggers worktree/port allocation on IN_PROGRESS.
        Auto-releases resources on DONE.

        Returns:
            {"success": bool, "card": dict, "message": str}
        """
        card = self._cards.get(card_id)
        if not card:
            return {"success": False, "message": f"Card {card_id} not found"}

        try:
            current = CardStatus(card.status)
            target = CardStatus(target_status)
        except ValueError:
            return {"success": False, "message": f"Invalid status: {target_status}"}

        if target not in TRANSITIONS.get(current, []):
            return {
                "success": False,
                "message": f"Invalid transition: {current.value} → {target.value}. "
                           f"Allowed: {[t.value for t in TRANSITIONS[current]]}"
            }

        old_status = card.status
        card.status = target.value
        card.updated_at = datetime.now().isoformat()

        # --- Side effects ---

        if target == CardStatus.IN_PROGRESS:
            self._on_start(card)

        if target == CardStatus.DONE:
            card.completed_at = datetime.now().isoformat()
            self._on_complete(card)

        card.history.append({
            "action": "moved",
            "timestamp": card.updated_at,
            "details": f"{old_status} → {target.value}",
        })

        self._save()
        logger.info(f"[Kanban] {card_id} moved: {old_status} → {target.value}")
        return {"success": True, "card": card.to_dict(), "message": "OK"}

    def _on_start(self, card: KanbanCard):
        """Auto-allocate worktree and port when card enters IN_PROGRESS."""
        # Worktree allocation
        try:
            from swarm_v2.core.worktree_manager import create_worktree
            branch = f"task/{card.card_id}"
            wt_path = create_worktree(branch)
            card.worktree_path = wt_path
            logger.info(f"[Kanban] Worktree created: {wt_path}")
        except Exception as e:
            logger.debug(f"[Kanban] Worktree skipped: {e}")

        # Port allocation
        try:
            from swarm_v2.core.port_manager import PortManager
            pm = PortManager()
            port = pm.acquire_port(card.assignee or "kanban", card.card_id)
            card.allocated_port = port
            logger.info(f"[Kanban] Port allocated: {port}")
        except Exception as e:
            logger.debug(f"[Kanban] Port allocation skipped: {e}")

    def _on_complete(self, card: KanbanCard):
        """Release resources when card is done."""
        if card.allocated_port:
            try:
                from swarm_v2.core.port_manager import PortManager
                pm = PortManager()
                pm.release_port(card.allocated_port)
                logger.info(f"[Kanban] Port {card.allocated_port} released")
            except Exception:
                pass

        if card.worktree_path:
            try:
                from swarm_v2.core.worktree_manager import remove_worktree
                remove_worktree(card.worktree_path)
                logger.info(f"[Kanban] Worktree removed: {card.worktree_path}")
            except Exception:
                pass

    def assign_card(self, card_id: str, assignee: str) -> bool:
        """Assign a card to an agent."""
        card = self._cards.get(card_id)
        if not card:
            return False
        card.assignee = assignee
        card.updated_at = datetime.now().isoformat()
        card.history.append({
            "action": "assigned",
            "timestamp": card.updated_at,
            "details": f"Assigned to {assignee}",
        })
        self._save()
        return True

    def archive_card(self, card_id: str) -> bool:
        """Move a completed card to the archive."""
        return self.move_card(card_id, "ARCHIVED").get("success", False)

    def get_card(self, card_id: str) -> Optional[Dict[str, Any]]:
        """Get a single card."""
        card = self._cards.get(card_id)
        return card.to_dict() if card else None

    def get_board(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get the full board grouped by columns."""
        board = {status.value: [] for status in CardStatus}

        for card in self._cards.values():
            col = card.status
            if col in board:
                board[col].append(card.to_dict())
            else:
                board[col] = [card.to_dict()]

        # Sort each column by priority
        for col in board:
            board[col].sort(key=lambda c: PRIORITY_ORDER.get(c.get("priority", "medium"), 2))

        return board

    def get_column(self, status: str) -> List[Dict[str, Any]]:
        """Get cards in a specific column."""
        return [c.to_dict() for c in self._cards.values() if c.status == status]

    def get_agent_cards(self, assignee: str) -> List[Dict[str, Any]]:
        """Get all cards assigned to an agent."""
        return [c.to_dict() for c in self._cards.values()
                if c.assignee == assignee and c.status != "ARCHIVED"]

    def get_stats(self) -> Dict[str, Any]:
        """Board statistics."""
        by_status = {}
        for card in self._cards.values():
            by_status[card.status] = by_status.get(card.status, 0) + 1

        return {
            "total_cards": len(self._cards),
            "by_status": by_status,
            "in_progress_count": by_status.get("IN_PROGRESS", 0),
            "active_worktrees": sum(1 for c in self._cards.values()
                                    if c.worktree_path and c.status == "IN_PROGRESS"),
            "active_ports": sum(1 for c in self._cards.values()
                                if c.allocated_port and c.status == "IN_PROGRESS"),
        }


# Singleton
_board: Optional[KanbanBoard] = None

def get_kanban_board() -> KanbanBoard:
    global _board
    if _board is None:
        _board = KanbanBoard()
    return _board
