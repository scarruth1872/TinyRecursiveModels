"""
TRM Orchestrator - Enhanced TRM Brain with Recursive Sub-Agent Spawning

Implements:
1. Recursive context processing with sub-agent spawning
2. Stateful superposition across parallel reasoning threads
3. Resource-aware scheduling for CPU/GPU/RAM utilization
4. Consensus mechanism for competing interpretations
"""

import asyncio
import threading
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import concurrent.futures
import psutil

from swarm_v2.core.trm_brain import TRMBrain, get_trm_brain
from swarm_v2.core.task_arbiter import get_task_arbiter, TaskComplexity, ComputeTarget
from swarm_v2.core.base_agent import BaseAgent, AgentPersona

class SuperpositionState:
    """Manages competing interpretations in a coherent belief state."""
    
    def __init__(self):
        self.interpretations: List[Dict] = []
        self.confidences: List[float] = []
        self.latent_z = None  # Shared latent state
        self.collapsed_result = None
        self.collapsed_at = None
        
    def add_interpretation(self, interpretation: Dict, confidence: float):
        """Add a competing interpretation with confidence score."""
        self.interpretations.append(interpretation)
        self.confidences.append(confidence)
        
    def merge(self, other: 'SuperpositionState'):
        """Merge another superposition state into this one."""
        self.interpretations.extend(other.interpretations)
        self.confidences.extend(other.confidences)
        
        # If other has latent state, prefer it if we don't have one
        if other.latent_z is not None and self.latent_z is None:
            self.latent_z = other.latent_z
            
    def collapse(self, threshold: float = 0.8) -> Optional[Dict]:
        """
        Collapse competing interpretations into final answer.
        
        Args:
            threshold: Minimum confidence required for collapse
            
        Returns:
            Collapsed interpretation or None if not enough confidence
        """
        if not self.interpretations:
            return None
            
        # Check if any interpretation exceeds threshold
        max_confidence = max(self.confidences) if self.confidences else 0
        if max_confidence < threshold:
            return None
            
        # Find the interpretation with highest confidence
        max_idx = self.confidences.index(max_confidence)
        result = self.interpretations[max_idx].copy()
        result["confidence"] = max_confidence
        result["alternative_count"] = len(self.interpretations)
        
        self.collapsed_result = result
        self.collapsed_at = time.time()
        
        return result
        
    def get_consensus(self) -> Optional[Dict]:
        """Get weighted consensus across all interpretations."""
        if not self.interpretations:
            return None
            
        # Normalize confidences
        total = sum(self.confidences)
        if total == 0:
            return None
            
        weights = [c/total for c in self.confidences]
        
        # Simple weighted aggregation (for now)
        # In practice, this would be more sophisticated
        consensus = {
            "interpretations": len(self.interpretations),
            "avg_confidence": sum(self.confidences) / len(self.confidences),
            "max_confidence": max(self.confidences),
            "state": "superposed" if not self.collapsed_result else "collapsed"
        }
        
        return consensus


class SubAgentTask:
    """Represents a sub-agent reasoning task."""
    
    def __init__(self, 
                 task_id: str,
                 context: str,
                 parent_state: Optional[SuperpositionState] = None,
                 compute_target: ComputeTarget = ComputeTarget.CPU_CORES):
        self.task_id = task_id
        self.context = context
        self.parent_state = parent_state
        self.compute_target = compute_target
        self.result: Optional[Dict] = None
        self.error: Optional[str] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.assigned_cpu_cores: List[int] = []
        self.assigned_gpu_memory: Optional[int] = None


class TRMOrchestrator:
    """
    Manages recursive spawning of sub-agents for parallel reasoning.
    
    Features:
    - Recursive context partitioning
    - Parallel sub-agent execution
    - State synchronization
    - Resource-aware scheduling
    - Consensus building
    """
    
    def __init__(self, base_agent: Optional[BaseAgent] = None):
        self.base_agent = base_agent
        self.trm_brain = get_trm_brain()
        self.task_arbiter = get_task_arbiter()
        self.subagents: Dict[str, BaseAgent] = {}
        self.active_tasks: Dict[str, SubAgentTask] = {}
        self.superposition_states: Dict[str, SuperpositionState] = {}
        
        # Resource tracking
        self.available_cpu_cores = self._detect_available_cores()
        self.available_gpu_memory = self._estimate_gpu_memory()
        self.max_parallel_tasks = min(len(self.available_cpu_cores) * 2, 16)
        
        # Performance metrics
        self.metrics = {
            "total_tasks": 0,
            "parallel_tasks": 0,
            "avg_response_time": 0,
            "resource_utilization": {},
            "error_rate": 0
        }
        
    def _detect_available_cores(self) -> List[int]:
        """Detect available CPU cores for pinning."""
        total_cores = psutil.cpu_count(logical=True)
        # Reserve 2 cores for OS/system
        available = list(range(2, total_cores)) if total_cores > 2 else list(range(total_cores))
        return available
        
    def _estimate_gpu_memory(self) -> Optional[int]:
        """Estimate available GPU memory in MB."""
        try:
            import torch
            if torch.cuda.is_available():
                return torch.cuda.get_device_properties(0).total_memory // (1024 * 1024)
        except:
            pass
        return None
        
    def partition_context(self, context: str, num_partitions: int) -> List[str]:
        """
        Partition context for parallel processing.
        
        For text context, uses semantic boundaries.
        For symbolic context, uses equal partitioning.
        """
        if not context:
            return []
            
        # Count newlines
        lines = context.split('\n')
        
        if len(lines) > 1:
            # Multiple lines: partition by lines
            if len(lines) > num_partitions:
                # More lines than partitions: group lines
                partition_size = len(lines) // num_partitions
                partitions = []
                for i in range(num_partitions):
                    start = i * partition_size
                    end = (i + 1) * partition_size if i < num_partitions - 1 else len(lines)
                    partition = '\n'.join(lines[start:end])
                    if partition:
                        partitions.append(partition)
                return partitions
            else:
                # Fewer lines than partitions: each line gets its own partition
                return [line for line in lines if line.strip()]
        else:
            # Single line: need smarter partitioning
            line = lines[0]
            
            # Check if it's symbolic (mostly numbers and spaces)
            numeric_chars = sum(1 for c in line if c.isdigit() or c.isspace())
            is_symbolic = numeric_chars / len(line) > 0.7
            
            if is_symbolic:
                # Symbolic: split by spaces
                tokens = line.split()
                if len(tokens) > num_partitions:
                    # Group tokens
                    token_partition_size = len(tokens) // num_partitions
                    partitions = []
                    for i in range(num_partitions):
                        start = i * token_partition_size
                        end = (i + 1) * token_partition_size if i < num_partitions - 1 else len(tokens)
                        partition = ' '.join(tokens[start:end])
                        if partition:
                            partitions.append(partition)
                    return partitions
                else:
                    # Fewer tokens than partitions: each token gets its own partition
                    return [token for token in tokens if token]
            else:
                # Text: split by sentences or equal chunks
                # Simple approach: split by spaces
                words = line.split()
                if len(words) > num_partitions * 5:  # At least 5 words per partition
                    # Group words
                    words_per_partition = len(words) // num_partitions
                    partitions = []
                    for i in range(num_partitions):
                        start = i * words_per_partition
                        end = (i + 1) * words_per_partition if i < num_partitions - 1 else len(words)
                        partition = ' '.join(words[start:end])
                        if partition:
                            partitions.append(partition)
                    return partitions
                else:
                    # Not enough words for meaningful partitioning
                    # Return equal character chunks
                    chunk_size = len(line) // num_partitions
                    if chunk_size < 10:  # Too small chunks
                        return [line]  # Don't partition
                    
                    partitions = []
                    for i in range(num_partitions):
                        start = i * chunk_size
                        end = (i + 1) * chunk_size if i < num_partitions - 1 else len(line)
                        partition = line[start:end]
                        if partition:
                            partitions.append(partition)
                    return partitions
            
    def create_subagent(self, 
                       parent_agent: BaseAgent,
                       role: str,
                       task: str) -> BaseAgent:
        """Create a lightweight sub-agent with inherited skills."""
        sub_persona = AgentPersona(
            name=f"{parent_agent.persona.name}_Sub{len(parent_agent.subagents) + 1}",
            role=role,
            background=f"Spawned by {parent_agent.persona.name} for parallel reasoning",
            specialties=parent_agent.persona.specialties[:2],
            avatar_color="#ffaa00"
        )
        
        # Inherit skills from parent
        sub_agent = BaseAgent(
            persona=sub_persona,
            skills=list(parent_agent.skills)
        )
        
        # Inherit memory context
        sub_agent.memory = parent_agent.memory  # Shared memory for now
        
        parent_agent.subagents[sub_agent.agent_id] = sub_agent
        self.subagents[sub_agent.agent_id] = sub_agent
        
        return sub_agent
        
    async def spawn_sub_reasoning(self,
                                 context: str,
                                 depth: int = 0,
                                 max_depth: int = 3,
                                 confidence_threshold: float = 0.8) -> Dict[str, Any]:
        """
        Recursively spawn sub-reasoning tasks.
        
        Args:
            context: The context to reason about
            depth: Current recursion depth
            max_depth: Maximum recursion depth
            confidence_threshold: Confidence required for collapse
            
        Returns:
            Dictionary with reasoning results
        """
        task_id = f"trm_recursive_{int(time.time())}_{depth}"
        superposition = SuperpositionState()
        self.superposition_states[task_id] = superposition
        
        # Check termination conditions
        if depth >= max_depth:
            return {"status": "max_depth_reached", "depth": depth}
            
        # Partition context for parallel processing
        partitions = self.partition_context(context, self.max_parallel_tasks)
        if not partitions:
            return {"status": "no_partitions", "context": context}
            
        # Create sub-tasks
        sub_tasks = []
        for i, partition in enumerate(partitions):
            sub_task_id = f"{task_id}_{i}"
            sub_task = SubAgentTask(
                task_id=sub_task_id,
                context=partition,
                parent_state=superposition,
                compute_target=ComputeTarget.CPU_CORES  # Default
            )
            sub_tasks.append(sub_task)
            self.active_tasks[sub_task_id] = sub_task
            
        # Execute sub-tasks in parallel
        results = await self._execute_parallel(sub_tasks, depth)
        
        # Merge results into superposition
        for result in results:
            if result and "interpretation" in result:
                confidence = result.get("confidence", 0.5)
                superposition.add_interpretation(
                    result["interpretation"],
                    confidence
                )
                
        # Check for collapse
        collapsed = superposition.collapse(threshold=confidence_threshold)
        if collapsed:
            return {
                "status": "collapsed",
                "result": collapsed,
                "depth": depth,
                "parallel_tasks": len(sub_tasks)
            }
            
        # Recursive continuation with refined context
        if depth < max_depth - 1:
            # Merge all interpretations for next round
            merged_context = self._merge_contexts(results)
            return await self.spawn_sub_reasoning(
                merged_context,
                depth + 1,
                max_depth,
                confidence_threshold
            )
            
        return {
            "status": "inconclusive",
            "superposition": superposition.get_consensus(),
            "depth": depth,
            "parallel_tasks": len(sub_tasks)
        }
        
    async def _execute_parallel(self, 
                              sub_tasks: List[SubAgentTask],
                              depth: int) -> List[Optional[Dict]]:
        """Execute sub-tasks in parallel with resource allocation."""
        # Allocate resources
        self._allocate_resources(sub_tasks)
        
        # Create executor with limited parallelism
        max_workers = min(len(sub_tasks), self.max_parallel_tasks)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit tasks
            future_to_task = {}
            for sub_task in sub_tasks:
                future = executor.submit(
                    self._execute_single_task,
                    sub_task,
                    depth
                )
                future_to_task[future] = sub_task
                
            # Collect results
            results = []
            for future in concurrent.futures.as_completed(future_to_task.keys()):
                sub_task = future_to_task[future]
                try:
                    result = future.result()
                    sub_task.result = result
                    results.append(result)
                except Exception as e:
                    sub_task.error = str(e)
                    results.append(None)
                    
        # Update metrics
        self._update_metrics(sub_tasks)
        
        # Release resources
        self._release_resources(sub_tasks)
        
        return results
        
    def _execute_single_task(self, sub_task: SubAgentTask, depth: int) -> Dict:
        """Execute a single sub-task with TRM reasoning."""
        sub_task.start_time = time.time()
        
        try:
            # Use TRM brain for reasoning
            # Convert context to tokens if needed
            if self._looks_like_symbolic(sub_task.context):
                tokens = self._context_to_tokens(sub_task.context)
                result_tokens = self.trm_brain.reason(tokens)
                interpretation = {
                    "type": "symbolic",
                    "tokens": result_tokens[:len(tokens)],
                    "original_length": len(tokens)
                }
            else:
                # Text-based reasoning
                interpretation = {
                    "type": "text",
                    "content": sub_task.context,
                    "processed": True
                }
                
            # Calculate confidence based on processing depth
            confidence = 0.7 - (depth * 0.1)  # Deeper recursion = less confidence
            confidence = max(0.3, min(0.9, confidence))
            
            sub_task.end_time = time.time()
            
            return {
                "interpretation": interpretation,
                "confidence": confidence,
                "task_id": sub_task.task_id,
                "processing_time": sub_task.end_time - sub_task.start_time
            }
            
        except Exception as e:
            sub_task.error = str(e)
            sub_task.end_time = time.time()
            return {
                "error": str(e),
                "task_id": sub_task.task_id,
                "processing_time": sub_task.end_time - sub_task.start_time
            }
            
    def _allocate_resources(self, sub_tasks: List[SubAgentTask]):
        """Allocate CPU cores and GPU memory to sub-tasks."""
        # Simple round-robin allocation
        cpu_idx = 0
        for sub_task in sub_tasks:
            if cpu_idx < len(self.available_cpu_cores):
                sub_task.assigned_cpu_cores = [self.available_cpu_cores[cpu_idx]]
                cpu_idx += 1
                
            # Allocate GPU memory for complex tasks
            if sub_task.compute_target == ComputeTarget.GPU_MODEL:
                if self.available_gpu_memory and self.available_gpu_memory > 512:  # 512MB minimum
                    sub_task.assigned_gpu_memory = 512  # Allocate 512MB per task
                    
    def _release_resources(self, sub_tasks: List[SubAgentTask]):
        """Release allocated resources."""
        # Resources are automatically released when tasks complete
        pass
        
    def _update_metrics(self, sub_tasks: List[SubAgentTask]):
        """Update performance metrics."""
        completed = [t for t in sub_tasks if t.end_time]
        if not completed:
            return
            
        # Calculate average response time
        times = [t.end_time - t.start_time for t in completed if t.start_time and t.end_time]
        if times:
            avg_time = sum(times) / len(times)
            self.metrics["avg_response_time"] = (self.metrics["avg_response_time"] * 0.9 + 
                                                avg_time * 0.1)
            
        # Update error rate
        errors = sum(1 for t in completed if t.error)
        error_rate = errors / len(completed)
        self.metrics["error_rate"] = (self.metrics["error_rate"] * 0.9 + 
                                     error_rate * 0.1)
        
        self.metrics["total_tasks"] += len(completed)
        self.metrics["parallel_tasks"] = max(self.metrics["parallel_tasks"], len(sub_tasks))
        
    def _looks_like_symbolic(self, context: str) -> bool:
        """Check if context looks like symbolic tokens."""
        # Simple heuristic: mostly numbers and spaces
        if not context:
            return False
        numeric_chars = sum(1 for c in context if c.isdigit() or c.isspace())
        return numeric_chars / len(context) > 0.7
        
    def _context_to_tokens(self, context: str) -> List[int]:
        """Convert symbolic context to token list."""
        tokens = []
        for part in context.split():
            try:
                tokens.append(int(part))
            except ValueError:
                # Use hash as fallback
                tokens.append(abs(hash(part)) % 10)
        return tokens
        
    def _merge_contexts(self, results: List[Optional[Dict]]) -> str:
        """Merge multiple reasoning results into single context."""
        merged_parts = []
        for result in results:
            if not result or "interpretation" not in result:
                continue
                
            interpretation = result["interpretation"]
            if interpretation["type"] == "symbolic":
                tokens = interpretation.get("tokens", [])
                merged_parts.append(" ".join(map(str, tokens)))
            else:
                content = interpretation.get("content", "")
                if content:
                    merged_parts.append(content)
                    
        return "\n".join(merged_parts)
        
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        return {
            "active_tasks": len(self.active_tasks),
            "subagents": len(self.subagents),
            "available_cores": len(self.available_cpu_cores),
            "gpu_memory_mb": self.available_gpu_memory,
            "max_parallel_tasks": self.max_parallel_tasks,
            "metrics": self.metrics.copy(),
            "superposition_states": len(self.superposition_states)
        }
        
    def cleanup(self):
        """Clean up resources and sub-agents."""
        self.active_tasks.clear()
        self.superposition_states.clear()
        
        # Clean up sub-agents
        for subagent_id in list(self.subagents.keys()):
            if subagent_id in self.subagents:
                del self.subagents[subagent_id]


# Singleton instance
_orchestrator = None

def get_trm_orchestrator(base_agent: Optional[BaseAgent] = None) -> TRMOrchestrator:
    """Get or create TRM orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TRMOrchestrator(base_agent)
    return _orchestrator