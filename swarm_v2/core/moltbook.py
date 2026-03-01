"""
Moltbook — Agent-to-Agent Knowledge Exchange Network
Phase 7: Enables agents to post queries, share solutions, and build
a collective knowledge graph within (and eventually across) the swarm.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("Moltbook")


@dataclass
class MoltbookQuery:
    """A query posted to the Moltbook network."""
    query_id: str
    author: str
    question: str
    tags: List[str] = field(default_factory=list)
    responses: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "open"  # open, resolved, expired
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved_at: Optional[str] = None


class MoltbookNetwork:
    """
    Agent-to-Agent social knowledge network.

    Agents post problems they can't solve, other agents with matching
    specialties respond. Solutions are persisted to GlobalMemorySync
    and tagged for future retrieval.
    """

    def __init__(self):
        self._queries: Dict[str, MoltbookQuery] = {}
        self._agent_profiles: Dict[str, Dict[str, Any]] = {}
        self._stats = {
            "total_queries": 0,
            "total_responses": 0,
            "resolved": 0,
        }

    def register_agent(self, agent_id: str, specialties: List[str],
                       capabilities: List[str] = None):
        """Register an agent's profile for query matching."""
        self._agent_profiles[agent_id] = {
            "specialties": specialties,
            "capabilities": capabilities or [],
            "response_count": 0,
            "reputation": 0.5,
            "registered_at": datetime.now().isoformat(),
        }
        logger.info(f"[Moltbook] Agent {agent_id} registered with specialties: {specialties}")

    def post_query(self, author: str, question: str,
                   tags: List[str] = None) -> str:
        """
        Post a problem to the Moltbook network.

        Args:
            author: Agent posting the query
            question: The problem description
            tags: Topic tags for matching

        Returns:
            query_id
        """
        query_id = f"molt-{uuid.uuid4().hex[:8]}"
        query = MoltbookQuery(
            query_id=query_id,
            author=author,
            question=question,
            tags=tags or [],
        )
        self._queries[query_id] = query
        self._stats["total_queries"] += 1

        logger.info(f"[Moltbook] Query posted by {author}: {question[:60]}... (tags={tags})")
        return query_id

    def respond_to_query(self, query_id: str, responder: str,
                         solution: str, confidence: float = 0.5) -> bool:
        """
        Respond to an open query with a solution.

        Args:
            query_id: ID of the query to respond to
            responder: Agent providing the response
            solution: The proposed solution
            confidence: Self-reported confidence (0-1)

        Returns:
            True if response was accepted
        """
        query = self._queries.get(query_id)
        if not query or query.status != "open":
            return False

        response = {
            "responder": responder,
            "solution": solution,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }
        query.responses.append(response)
        self._stats["total_responses"] += 1

        # Update responder reputation
        if responder in self._agent_profiles:
            self._agent_profiles[responder]["response_count"] += 1

        logger.info(f"[Moltbook] {responder} responded to {query_id} "
                    f"(confidence={confidence:.2f})")
        return True

    def resolve_query(self, query_id: str, accepted_response_idx: int = 0) -> Optional[Dict]:
        """
        Mark a query as resolved, accepting the best response.

        Args:
            query_id: Query to resolve
            accepted_response_idx: Index of the accepted response

        Returns:
            The accepted response, or None
        """
        query = self._queries.get(query_id)
        if not query or not query.responses:
            return None

        idx = min(accepted_response_idx, len(query.responses) - 1)
        accepted = query.responses[idx]

        query.status = "resolved"
        query.resolved_at = datetime.now().isoformat()
        self._stats["resolved"] += 1

        # Boost responder reputation
        responder = accepted["responder"]
        if responder in self._agent_profiles:
            profile = self._agent_profiles[responder]
            profile["reputation"] = min(1.0, profile["reputation"] + 0.05)

        logger.info(f"[Moltbook] Query {query_id} resolved. "
                    f"Accepted solution from {responder}")

        # Persist to GlobalMemory if available
        self._persist_to_memory(query, accepted)

        return accepted

    def find_matching_queries(self, agent_id: str,
                              limit: int = 5) -> List[MoltbookQuery]:
        """
        Find open queries matching an agent's specialties.

        Args:
            agent_id: The agent looking for queries to answer
            limit: Max queries to return
        """
        profile = self._agent_profiles.get(agent_id, {})
        specialties = set(s.lower() for s in profile.get("specialties", []))

        if not specialties:
            # Return all open queries if no specialties known
            return [q for q in self._queries.values()
                    if q.status == "open"][:limit]

        matched = []
        for query in self._queries.values():
            if query.status != "open" or query.author == agent_id:
                continue
            query_tags = set(t.lower() for t in query.tags)
            if query_tags & specialties:
                matched.append(query)

        return matched[:limit]

    def get_feed(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent Moltbook activity feed."""
        recent = sorted(
            self._queries.values(),
            key=lambda q: q.created_at,
            reverse=True,
        )[:limit]

        return [{
            "query_id": q.query_id,
            "author": q.author,
            "question": q.question[:100],
            "tags": q.tags,
            "status": q.status,
            "response_count": len(q.responses),
            "created_at": q.created_at,
        } for q in recent]

    def install_solution(self, query_id: str, target_agent: str) -> Optional[str]:
        """
        Install an accepted solution into a target agent's context.

        Args:
            query_id: Resolved query to pull solution from
            target_agent: Agent importing the solution

        Returns:
            The solution text, or None
        """
        query = self._queries.get(query_id)
        if not query or query.status != "resolved":
            return None

        # Find the accepted response (highest confidence among responses)
        best = max(query.responses, key=lambda r: r.get("confidence", 0))
        logger.info(f"[Moltbook] {target_agent} installed solution from "
                    f"{best['responder']} for query {query_id}")
        return best["solution"]

    def _persist_to_memory(self, query: MoltbookQuery, solution: Dict):
        """Persist resolved query-solution pair to GlobalMemory."""
        try:
            from swarm_v2.core.global_memory import get_global_memory
            gm = get_global_memory()
            gm.contribute(
                content=f"Q: {query.question}\nA: {solution['solution']}",
                author=solution["responder"],
                author_role="moltbook_contributor",
                memory_type="moltbook",
                tags=["moltbook", "knowledge_exchange"] + query.tags,
            )
        except Exception as e:
            logger.debug(f"[Moltbook] Could not persist to GlobalMemory: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get Moltbook network statistics."""
        return {
            "registered_agents": len(self._agent_profiles),
            "open_queries": sum(1 for q in self._queries.values() if q.status == "open"),
            **self._stats,
            "top_contributors": sorted(
                [(aid, p.get("response_count", 0), p.get("reputation", 0.5))
                 for aid, p in self._agent_profiles.items()],
                key=lambda x: x[1], reverse=True
            )[:5],
        }


# Singleton
_network: Optional[MoltbookNetwork] = None

def get_moltbook_network() -> MoltbookNetwork:
    global _network
    if _network is None:
        _network = MoltbookNetwork()
    return _network
