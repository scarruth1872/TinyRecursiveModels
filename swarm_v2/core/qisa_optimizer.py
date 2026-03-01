"""
Quantum-Inspired Simulated Annealing (QISA) Optimizer
Phase 7: Enables agents to escape local optima via quantum tunneling during planning.

Uses temperature-based acceptance of worse solutions combined with periodic
perturbations to the QState tensor, simulating quantum tunneling through
energy barriers in the solution landscape.
"""

import math
import random
import logging
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("QISAOptimizer")

try:
    import torch
    from swarm_v2.core.qic._state import QState, QOperator, ManusProtocol
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


@dataclass
class AnnealingConfig:
    """Configuration for the QISA annealing process."""
    initial_temperature: float = 1.0
    cooling_rate: float = 0.95       # Multiplicative cooling per cycle
    min_temperature: float = 0.01
    max_cycles: int = 50
    tunnel_probability: float = 0.15  # Chance of quantum tunnel per cycle
    tunnel_strength: float = 0.3      # Magnitude of tunneling perturbation
    convergence_threshold: float = 0.001  # Stop if improvement < this


@dataclass
class AnnealingResult:
    """Result of a QISA optimization run."""
    best_index: int
    best_score: float
    initial_best_score: float
    cycles_run: int
    tunneling_events: int
    temperature_final: float
    history: List[Dict[str, Any]] = field(default_factory=list)

    def improvement_pct(self) -> float:
        if self.initial_best_score == 0:
            return 0.0
        return ((self.best_score - self.initial_best_score)
                / abs(self.initial_best_score)) * 100


class QISAOptimizer:
    """
    Quantum-Inspired Simulated Annealing Optimizer.

    Accepts candidate solution scores and uses annealing + quantum tunneling
    to explore the solution space beyond local optima.

    Can operate in two modes:
    1. Score-based: optimize over a list of numeric scores
    2. QState-based: perturb a ManusProtocol QState tensor directly
    """

    def __init__(self, config: Optional[AnnealingConfig] = None):
        self.config = config or AnnealingConfig()
        self._run_count = 0
        self._total_tunnels = 0
        self._history: List[AnnealingResult] = []

    def optimize(self, scores: List[float],
                 score_fn: Optional[Callable[[int], float]] = None) -> AnnealingResult:
        """
        Optimize over a list of candidate scores using simulated annealing
        with quantum tunneling.

        Args:
            scores: Initial quality scores for each candidate
            score_fn: Optional function to re-evaluate a candidate (index -> score)

        Returns:
            AnnealingResult with the best candidate index and optimization metadata
        """
        if not scores:
            raise ValueError("Cannot optimize empty score list")

        cfg = self.config
        n = len(scores)
        current_scores = list(scores)
        current_best_idx = max(range(n), key=lambda i: current_scores[i])
        current_best_score = current_scores[current_best_idx]
        initial_best_score = current_best_score

        temperature = cfg.initial_temperature
        tunneling_events = 0
        history = []

        for cycle in range(cfg.max_cycles):
            if temperature < cfg.min_temperature:
                break

            # --- Quantum Tunneling ---
            # With some probability, perturb a random candidate's score
            # This simulates tunneling through energy barriers
            if random.random() < cfg.tunnel_probability:
                tunnel_idx = random.randint(0, n - 1)
                perturbation = random.gauss(0, cfg.tunnel_strength)

                if score_fn:
                    # Re-evaluate with perturbation as exploration signal
                    new_score = score_fn(tunnel_idx) + perturbation
                else:
                    new_score = current_scores[tunnel_idx] + perturbation

                current_scores[tunnel_idx] = max(0.0, new_score)
                tunneling_events += 1
                logger.debug(f"[QISA] Tunnel at idx={tunnel_idx}: "
                             f"{scores[tunnel_idx]:.3f} → {current_scores[tunnel_idx]:.3f}")

            # --- Simulated Annealing Step ---
            # Pick a random neighbor and decide whether to accept it
            candidate_idx = random.randint(0, n - 1)
            candidate_score = current_scores[candidate_idx]
            delta = candidate_score - current_best_score

            if delta > 0:
                # Better solution — always accept
                current_best_idx = candidate_idx
                current_best_score = candidate_score
            else:
                # Worse solution — accept with probability exp(delta/T)
                acceptance_prob = math.exp(delta / max(temperature, 1e-10))
                if random.random() < acceptance_prob:
                    current_best_idx = candidate_idx
                    current_best_score = candidate_score
                    logger.debug(f"[QISA] Accepted worse solution "
                                 f"(Δ={delta:.3f}, p={acceptance_prob:.3f}, T={temperature:.3f})")

            # Record cycle
            history.append({
                "cycle": cycle,
                "temperature": round(temperature, 4),
                "best_idx": current_best_idx,
                "best_score": round(current_best_score, 4),
                "tunneled": tunneling_events > (len(history) and
                            history[-1].get("tunneled", 0) if history else 0),
            })

            # --- Cooling ---
            temperature *= cfg.cooling_rate

            # --- Convergence check ---
            if (len(history) >= 5 and
                abs(history[-1]["best_score"] - history[-5]["best_score"])
                    < cfg.convergence_threshold):
                logger.info(f"[QISA] Converged at cycle {cycle}")
                break

        result = AnnealingResult(
            best_index=current_best_idx,
            best_score=current_best_score,
            initial_best_score=initial_best_score,
            cycles_run=len(history),
            tunneling_events=tunneling_events,
            temperature_final=temperature,
            history=history,
        )

        self._run_count += 1
        self._total_tunnels += tunneling_events
        self._history.append(result)

        logger.info(f"[QISA] Optimization complete: best_idx={result.best_index}, "
                    f"score={result.best_score:.3f}, "
                    f"improvement={result.improvement_pct():.1f}%, "
                    f"tunnels={tunneling_events}, cycles={result.cycles_run}")

        return result

    def optimize_qstate(self, task_id: str, protocol: 'ManusProtocol') -> AnnealingResult:
        """
        Optimize a ManusProtocol QState directly using QISA.
        Perturbs the probability tensor to escape local optima.

        Args:
            task_id: Task ID in the ManusProtocol registry
            protocol: The ManusProtocol instance holding the QState

        Returns:
            AnnealingResult with the best outcome index
        """
        if not HAS_TORCH:
            raise RuntimeError("PyTorch required for QState optimization")

        probs = protocol.get_probabilities(task_id)
        if probs is None:
            raise ValueError(f"No QState found for task_id={task_id}")

        scores = probs.tolist()

        def score_fn(idx: int) -> float:
            """Re-read probability from the live QState."""
            current = protocol.get_probabilities(task_id)
            return current[idx].item() if current is not None else 0.0

        result = self.optimize(scores, score_fn=score_fn)

        # Apply the optimization result back to the QState
        # Boost the winner's amplitude
        dim = len(scores)
        op = QOperator.create_priority_op(dim, result.best_index, weight=1.5)
        protocol.registry[task_id] = protocol.registry[task_id].apply_operator(op)

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get optimizer statistics."""
        return {
            "total_runs": self._run_count,
            "total_tunneling_events": self._total_tunnels,
            "avg_improvement_pct": (
                sum(r.improvement_pct() for r in self._history) / max(1, len(self._history))
            ),
            "config": {
                "initial_temperature": self.config.initial_temperature,
                "cooling_rate": self.config.cooling_rate,
                "tunnel_probability": self.config.tunnel_probability,
                "max_cycles": self.config.max_cycles,
            }
        }


# Singleton
_optimizer: Optional[QISAOptimizer] = None

def get_qisa_optimizer(config: Optional[AnnealingConfig] = None) -> QISAOptimizer:
    global _optimizer
    if _optimizer is None:
        _optimizer = QISAOptimizer(config)
    return _optimizer
