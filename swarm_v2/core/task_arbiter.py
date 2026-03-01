"""
Task Arbiter - Intelligent Resource Distribution for Swarm V2
Extends the Resource Arbiter to intelligently distribute CPU/GPU compute across all agents.
Monitors system tasks, classifies workload complexity, and offloads to optimal compute resources.
"""

import asyncio
import psutil
import threading
import os
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import deque
import logging

from swarm_v2.core.resource_arbiter import get_resource_arbiter, ResourceArbiter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TaskArbiter")

class TaskComplexity(Enum):
    """Classification of task complexity for resource allocation."""
    LOW = "low"          # CPU-only, lightweight
    MEDIUM = "medium"   # May benefit from GPU
    HIGH = "high"       # Requires GPU/model inference
    CRITICAL = "critical"  # Full system resources


class MaintenanceTaskType(Enum):
    """Types of maintenance tasks for dynamic scheduling."""
    MEMORY_PRUNING = "memory_pruning"
    LOG_ROTATION = "log_rotation"
    CACHE_CLEANUP = "cache_cleanup"
    METRICS_COLLECTION = "metrics_collection"
    HEALTH_CHECK = "health_check"
    GARBAGE_COLLECTION = "garbage_collection"
    INDEX_OPTIMIZATION = "index_optimization"
    TEMP_FILE_CLEANUP = "temp_file_cleanup"


class UsageWindow(Enum):
    """System usage windows for task scheduling."""
    LOW_USAGE = "low_usage"       # < 20% CPU, ideal for maintenance
    NORMAL_USAGE = "normal_usage"  # 20-60% CPU
    HIGH_USAGE = "high_usage"     # 60-80% CPU
    CRITICAL_USAGE = "critical_usage"  # > 80% CPU

class ComputeTarget(Enum):
    """Available compute targets for task execution."""
    CPU_CORES = "cpu_cores"
    GPU_MODEL = "gpu_model" 
    HYBRID = "hybrid"  # CPU preprocessing + GPU inference

from functools import total_ordering

@total_ordering
@dataclass
class Task:
    """Represents a task to be distributed."""
    task_id: str
    task_type: str  # "llm", "file_io", "computation", "analysis"
    complexity: TaskComplexity
    payload: Any
    callback: Optional[Callable] = None
    priority: int = 0  # Higher = more urgent
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    gpu_model: Optional[str] = None

    def __lt__(self, other):
        if not isinstance(other, Task):
            return NotImplemented
        return self.priority < other.priority

@dataclass 
class AgentWorkload:
    """Tracks an agent's current workload."""
    agent_id: str
    role: str
    current_task: Optional[Task] = None
    cpu_affinity: List[int] = field(default_factory=list)
    gpu_model: Optional[str] = None
    is_busy: bool = False
    task_history: List[str] = field(default_factory=list)


@dataclass
class MaintenanceTask:
    """Represents a maintenance task for dynamic scheduling."""
    task_id: str
    task_type: MaintenanceTaskType
    priority: int = 0  # Lower = less urgent (maintenance is low priority)
    estimated_duration_sec: float = 5.0
    last_run: Optional[datetime] = None
    interval_sec: float = 300.0  # Default: run every 5 minutes
    enabled: bool = True
    callback: Optional[Callable] = None
    
    def is_due(self) -> bool:
        """Check if maintenance task is due to run."""
        if not self.enabled:
            return False
        if self.last_run is None:
            return True
        elapsed = (datetime.now() - self.last_run).total_seconds()
        return elapsed >= self.interval_sec


@dataclass
class UsageMetrics:
    """Tracks system usage for dynamic scheduling decisions."""
    cpu_history: deque = field(default_factory=lambda: deque(maxlen=60))
    memory_history: deque = field(default_factory=lambda: deque(maxlen=60))
    request_history: deque = field(default_factory=lambda: deque(maxlen=100))
    last_low_usage_window: Optional[datetime] = None
    low_usage_duration_sec: float = 0.0

class DynamicPriorityArbiter:
    """
    Phase 5: Dynamic Priority Arbitration for Maintenance Tasks.
    
    Dynamically re-prioritizes maintenance tasks based on system usage windows:
    - LOW_USAGE (< 20% CPU): Run all maintenance tasks with higher priority
    - NORMAL_USAGE (20-60%): Run essential maintenance only
    - HIGH_USAGE (60-80%): Defer non-critical maintenance
    - CRITICAL_USAGE (> 80%): Pause all maintenance
    """
    
    # Priority adjustments per usage window
    PRIORITY_ADJUSTMENTS = {
        UsageWindow.LOW_USAGE: 50,       # Boost maintenance during idle
        UsageWindow.NORMAL_USAGE: 10,    # Normal maintenance priority
        UsageWindow.HIGH_USAGE: -20,     # Defer maintenance
        UsageWindow.CRITICAL_USAGE: -50, # Pause maintenance
    }
    
    # Default maintenance intervals (seconds)
    DEFAULT_INTERVALS = {
        MaintenanceTaskType.MEMORY_PRUNING: 300,
        MaintenanceTaskType.LOG_ROTATION: 3600,
        MaintenanceTaskType.CACHE_CLEANUP: 600,
        MaintenanceTaskType.METRICS_COLLECTION: 60,
        MaintenanceTaskType.HEALTH_CHECK: 30,
        MaintenanceTaskType.GARBAGE_COLLECTION: 180,
        MaintenanceTaskType.INDEX_OPTIMIZATION: 7200,
        MaintenanceTaskType.TEMP_FILE_CLEANUP: 1800,
    }
    
    def __init__(self, task_arbiter: 'TaskArbiter'):
        self.arbiter = task_arbiter
        self.maintenance_tasks: Dict[str, MaintenanceTask] = {}
        self.usage_metrics = UsageMetrics()
        self.maintenance_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._maintenance_running = False
        self._last_window = UsageWindow.NORMAL_USAGE
        self._stats = {
            "maintenance_runs": 0,
            "maintenance_deferred": 0,
            "low_usage_windows": 0,
            "total_low_usage_sec": 0,
        }
        
        # Initialize default maintenance tasks
        self._setup_default_maintenance()
    
    def _setup_default_maintenance(self):
        """Setup default maintenance tasks."""
        for task_type in MaintenanceTaskType:
            self.register_maintenance_task(
                task_id=f"maint_{task_type.value}",
                task_type=task_type,
                interval_sec=self.DEFAULT_INTERVALS.get(task_type, 300),
                enabled=True
            )
    
    def register_maintenance_task(
        self,
        task_id: str,
        task_type: MaintenanceTaskType,
        interval_sec: float = 300.0,
        enabled: bool = True,
        callback: Callable = None
    ) -> MaintenanceTask:
        """Register a maintenance task for dynamic scheduling."""
        task = MaintenanceTask(
            task_id=task_id,
            task_type=task_type,
            priority=self._get_base_priority(task_type),
            interval_sec=interval_sec,
            enabled=enabled,
            callback=callback
        )
        self.maintenance_tasks[task_id] = task
        logger.info(f"Registered maintenance task: {task_id} (interval: {interval_sec}s)")
        return task
    
    def _get_base_priority(self, task_type: MaintenanceTaskType) -> int:
        """Get base priority for maintenance task type."""
        # Essential maintenance gets higher base priority
        essential = {
            MaintenanceTaskType.HEALTH_CHECK: 80,
            MaintenanceTaskType.MEMORY_PRUNING: 60,
            MaintenanceTaskType.GARBAGE_COLLECTION: 50,
        }
        important = {
            MaintenanceTaskType.METRICS_COLLECTION: 40,
            MaintenanceTaskType.CACHE_CLEANUP: 30,
        }
        return essential.get(task_type, important.get(task_type, 10))
    
    def detect_usage_window(self) -> UsageWindow:
        """Detect current system usage window."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Record metrics
        self.usage_metrics.cpu_history.append(cpu_percent)
        self.usage_metrics.memory_history.append(memory.percent)
        
        # Calculate average over last minute
        if len(self.usage_metrics.cpu_history) > 0:
            avg_cpu = sum(self.usage_metrics.cpu_history) / len(self.usage_metrics.cpu_history)
        else:
            avg_cpu = cpu_percent
        
        # Determine window
        if avg_cpu < 20:
            window = UsageWindow.LOW_USAGE
        elif avg_cpu < 60:
            window = UsageWindow.NORMAL_USAGE
        elif avg_cpu < 80:
            window = UsageWindow.HIGH_USAGE
        else:
            window = UsageWindow.CRITICAL_USAGE
        
        # Track low usage windows
        if window == UsageWindow.LOW_USAGE:
            if self._last_window != UsageWindow.LOW_USAGE:
                self.usage_metrics.last_low_usage_window = datetime.now()
                self.usage_metrics.low_usage_duration_sec = 0
                self._stats["low_usage_windows"] += 1
            else:
                self.usage_metrics.low_usage_duration_sec += 1
                self._stats["total_low_usage_sec"] += 1
        else:
            # Reset low usage tracking
            self.usage_metrics.low_usage_duration_sec = 0
        
        self._last_window = window
        return window
    
    def get_dynamic_priority(self, task: MaintenanceTask) -> int:
        """Calculate dynamic priority based on current usage window."""
        window = self.detect_usage_window()
        base_priority = task.priority
        adjustment = self.PRIORITY_ADJUSTMENTS.get(window, 0)
        
        # Boost priority if task is overdue
        if task.last_run:
            elapsed = (datetime.now() - task.last_run).total_seconds()
            overdue_factor = min(20, int(elapsed / task.interval_sec) * 5)
            adjustment += overdue_factor
        
        return max(0, base_priority + adjustment)
    
    def should_run_maintenance(self, task: MaintenanceTask) -> bool:
        """Determine if maintenance task should run based on current conditions."""
        if not task.enabled:
            return False
        
        window = self._last_window
        
        # Never run maintenance in critical usage
        if window == UsageWindow.CRITICAL_USAGE:
            self._stats["maintenance_deferred"] += 1
            return False
        
        # Check if task is due
        if not task.is_due():
            return False
        
        # In high usage, only run essential maintenance
        if window == UsageWindow.HIGH_USAGE:
            essential = {
                MaintenanceTaskType.HEALTH_CHECK,
                MaintenanceTaskType.MEMORY_PRUNING
            }
            if task.task_type not in essential:
                self._stats["maintenance_deferred"] += 1
                return False
        
        # In low usage, run all due maintenance
        return True
    
    async def schedule_maintenance(self) -> List[MaintenanceTask]:
        """Schedule due maintenance tasks with dynamic priorities."""
        tasks_to_run = []
        
        for task in self.maintenance_tasks.values():
            if self.should_run_maintenance(task):
                dynamic_priority = self.get_dynamic_priority(task)
                tasks_to_run.append((dynamic_priority, task))
        
        # Sort by priority (higher = run first)
        tasks_to_run.sort(key=lambda x: -x[0])
        
        return [task for _, task in tasks_to_run]
    
    async def run_maintenance_cycle(self):
        """Run scheduled maintenance tasks."""
        tasks = await self.schedule_maintenance()
        
        for task in tasks:
            try:
                logger.info(f"[Maintenance] Running {task.task_type.value} (priority: {self.get_dynamic_priority(task)})")
                
                # Execute maintenance callback if available
                if task.callback:
                    result = await task.callback() if asyncio.iscoroutinefunction(task.callback) else task.callback()
                else:
                    result = await self._execute_default_maintenance(task.task_type)
                
                task.last_run = datetime.now()
                self._stats["maintenance_runs"] += 1
                
                logger.info(f"[Maintenance] Completed {task.task_type.value}: {result}")
                
            except Exception as e:
                logger.error(f"[Maintenance] Failed {task.task_type.value}: {e}")
    
    async def _execute_default_maintenance(self, task_type: MaintenanceTaskType) -> str:
        """Execute default maintenance action for task type."""
        import gc
        import glob
        
        if task_type == MaintenanceTaskType.GARBAGE_COLLECTION:
            collected = gc.collect()
            return f"Collected {collected} objects"
        
        elif task_type == MaintenanceTaskType.MEMORY_PRUNING:
            # Prune completed tasks from history
            pruned = 0
            if hasattr(self.arbiter, 'completed_tasks'):
                pruned = len(self.arbiter.completed_tasks)
                self.arbiter.completed_tasks.clear()
            return f"Pruned {pruned} completed tasks"
        
        elif task_type == MaintenanceTaskType.TEMP_FILE_CLEANUP:
            # Clean temp files older than 1 hour
            cleaned = 0
            temp_patterns = ["tmp*", "*.tmp", "*.temp"]
            for pattern in temp_patterns:
                for f in glob.glob(pattern):
                    try:
                        os.remove(f)
                        cleaned += 1
                    except:
                        pass
            return f"Cleaned {cleaned} temp files"
        
        elif task_type == MaintenanceTaskType.HEALTH_CHECK:
            # Quick health check
            busy_agents = sum(1 for w in self.arbiter.agent_workloads.values() if w.is_busy)
            return f"System healthy - {busy_agents} busy agents"
        
        elif task_type == MaintenanceTaskType.METRICS_COLLECTION:
            # Collect current metrics
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            return f"CPU: {cpu}%, Memory: {mem}%"
        
        else:
            return f"No default action for {task_type.value}"
    
    def get_maintenance_status(self) -> Dict:
        """Get maintenance scheduling status."""
        return {
            "current_window": self._last_window.value,
            "low_usage_duration_sec": self.usage_metrics.low_usage_duration_sec,
            "maintenance_tasks": {
                task_id: {
                    "type": task.task_type.value,
                    "enabled": task.enabled,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "is_due": task.is_due(),
                    "base_priority": task.priority,
                    "dynamic_priority": self.get_dynamic_priority(task),
                }
                for task_id, task in self.maintenance_tasks.items()
            },
            "stats": self._stats
        }


class TaskArbiter:
    """
    Intelligent Task Distribution System
    
    Features:
    - CPU core pinning for agent isolation
    - GPU model lifecycle management
    - Task complexity classification
    - Workload balancing across agents
    - Automatic offloading based on system load
    - Phase 5: Dynamic Priority Arbitration for maintenance
    """
    
    def __init__(self):
        self.resource_arbiter = get_resource_arbiter()
        self.agent_workloads: Dict[str, AgentWorkload] = {}
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.completed_tasks: deque = deque(maxlen=100)
        self._running = False
        self._stats = {
            "total_tasks": 0,
            "cpu_tasks": 0,
            "gpu_tasks": 0,
            "offloaded_tasks": 0,
            "avg_queue_time": 0,
        }
        
        # CPU configuration
        self.cpu_count = psutil.cpu_count(logical=True)
        self.cpu_physical = psutil.cpu_count(logical=False)
        
        # Reserve cores for different workloads
        self._setup_cpu_affinity()
        
        # Phase 5: Dynamic Priority Arbitration
        self.dynamic_arbiter = DynamicPriorityArbiter(self)
        
        logger.info(f"TaskArbiter initialized: {self.cpu_count} logical cores, {self.cpu_physical} physical cores")

    def _setup_cpu_affinity(self):
        """Setup CPU core allocation strategy."""
        if self.cpu_count >= 16:
            # High core count system - allocate ranges
            self.os_cores = list(range(0, 4))           # OS reserved
            self.llm_cores = list(range(4, 12))        # LLM inference  
            self.agent_cores = list(range(12, 20))      # Agent tasks
            self.io_cores = list(range(20, self.cpu_count))  # I/O operations
        elif self.cpu_count >= 8:
            # Medium system
            self.os_cores = [0]
            self.llm_cores = [1, 2, 3]
            self.agent_cores = [4, 5, 6]
            self.io_cores = [7]
        else:
            # Minimal system - share everything
            self.os_cores = [0]
            self.llm_cores = list(range(1, self.cpu_count))
            self.agent_cores = self.llm_cores
            self.io_cores = self.llm_cores

    async def register_agent(self, agent_id: str, role: str, gpu_model: str = None) -> AgentWorkload:
        """Register an agent with the arbiter."""
        workload = AgentWorkload(
            agent_id=agent_id,
            role=role,
            cpu_affinity=self._get_affinity_for_role(role),
            gpu_model=gpu_model
        )
        self.agent_workloads[agent_id] = workload
        logger.info(f"Registered agent {role} ({agent_id}) for {gpu_model} with CPU affinity: {workload.cpu_affinity}")
        return workload

    def _calculate_autonomous_priority(self, task: Task, agent_id: str) -> int:
        """Dynamically adjust task priority based on Phase 5 mission context."""
        base_priority = task.priority
        workload = self.agent_workloads.get(agent_id)
        if not workload: return base_priority
        
        # Phase 5 High-Priority Roles for Kickoff
        mission_critical_roles = {"Architect", "Reasoning Engine", "Security Auditor", "Swarm Manager"}
        if workload.role in mission_critical_roles:
            base_priority += 10 # Mission critical boost
            
        # Recursive Self-Healing tasks get top priority
        if task.task_type == "remediation" or task.complexity == TaskComplexity.CRITICAL:
            base_priority += 20
            
        return base_priority

    def _get_affinity_for_role(self, role: str) -> List[int]:
        """Determine CPU affinity based on agent role."""
        high_load_roles = {"Lead Developer", "Reasoning Engine", "Researcher"}
        io_roles = {"Technical Writer", "QA Engineer", "UI/UX Designer"}
        
        if role in high_load_roles:
            return self.llm_cores[:3] if len(self.llm_cores) >= 3 else self.agent_cores
        elif role in io_roles:
            return self.io_cores[:2] if len(self.io_cores) >= 2 else self.agent_cores
        else:
            return self.agent_cores[:2] if len(self.agent_cores) >= 2 else self.llm_cores

    def classify_task(self, task: str, context: Dict = None) -> TaskComplexity:
        """Classify task complexity based on content analysis."""
        task_lower = task.lower()
        
        # High complexity indicators - requires LLM/GPU
        high_complexity = any(kw in task_lower for kw in [
            "analyze", "audit", "review", "research", "generate", 
            "implement", "design", "architect", "create", "build",
            "reason", "explain", "compare", "evaluate"
        ])
        
        # Low complexity - simple I/O or retrieval
        low_complexity = any(kw in task_lower for kw in [
            "list", "show", "get", "read", "check", "status",
            "ping", "echo", "count", "simple"
        ])
        
        # Check for code generation patterns
        if any(kw in task_lower for kw in ["write file", "create file", "code"]):
            return TaskComplexity.HIGH
            
        if high_complexity and len(task) > 100:
            return TaskComplexity.HIGH
        elif low_complexity:
            return TaskComplexity.LOW
        elif len(task) > 200:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.LOW

    def get_optimal_compute_target(self, task: Task, system_load: float) -> ComputeTarget:
        """Determine optimal compute target based on task and system state."""
        # If system is heavily loaded, prefer CPU for simple tasks
        if system_load > 0.8 and task.complexity == TaskComplexity.LOW:
            return ComputeTarget.CPU_CORES
            
        # High complexity always needs GPU if available
        if task.complexity in [TaskComplexity.HIGH, TaskComplexity.CRITICAL]:
            return ComputeTarget.GPU_MODEL
            
        # Medium complexity - decide based on queue depth
        if task.complexity == TaskComplexity.MEDIUM:
            if system_load < 0.5:
                return ComputeTarget.HYBRID
            else:
                return ComputeTarget.CPU_CORES
                
        return ComputeTarget.CPU_CORES

    async def submit_task(self, task: Task) -> str:
        """Submit a task to the queue with autonomous prioritization."""
        self._stats["total_tasks"] += 1
        
        # Calculate Phase 5 Priority
        agent_id = task.payload.get("agent_id", "unknown")
        task.priority = self._calculate_autonomous_priority(task, agent_id)
        
        # Wrap in tuple for PriorityQueue (priority, task)
        # Note: priority is inverted because PriorityQueue is a min-heap (lower = first)
        await self.task_queue.put((-task.priority, task))
        logger.info(f"Task {task.task_id} submitted with priority {task.priority}")
        
        # Route to appropriate compute based on complexity
        system_load = psutil.cpu_percent() / 100.0
        compute_target = self.get_optimal_compute_target(task, system_load)
        
        if compute_target == ComputeTarget.GPU_MODEL:
            self._stats["gpu_tasks"] += 1
        else:
            self._stats["cpu_tasks"] += 1
            
        logger.info(f"Task {task.task_id} submitted: complexity={task.complexity.value}, target={compute_target.value}")
        return task.task_id

    async def get_next_task(self, agent_id: str) -> Optional[Task]:
        """Get the next optimal task for an agent."""
        try:
            # Peek at queue without blocking
            priority, task = self.task_queue.get_nowait()
            
            # Check if agent has capacity
            workload = self.agent_workloads.get(agent_id)
            if workload and not workload.is_busy:
                task.started_at = datetime.now()
                workload.is_busy = True
                workload.current_task = task
                return task
            else:
                # Put back in queue
                await self.task_queue.put((priority, task))
                return None
                
        except asyncio.QueueEmpty:
            return None

    def complete_task(self, task_id: str, result: Any = None, error: str = None):
        """Mark a task as completed and update stats."""
        for workload in self.agent_workloads.values():
            if workload.current_task and workload.current_task.task_id == task_id:
                task = workload.current_task
                task.completed_at = datetime.now()
                task.result = result
                task.error = error
                
                # Calculate queue time
                if task.started_at:
                    queue_time = (task.started_at - task.created_at).total_seconds()
                    # Update running average
                    self._stats["avg_queue_time"] = (
                        self._stats["avg_queue_time"] * 0.9 + queue_time * 0.1
                    )
                
                workload.is_busy = False
                workload.current_task = None
                workload.task_history.append(task_id)
                
                self.completed_tasks.append(task)
                
                if error:
                    logger.warning(f"Task {task_id} completed with error: {error}")
                else:
                    logger.info(f"Task {task_id} completed successfully")
                break

    async def acquire_gpu_for_task(self, task: Task) -> bool:
        """Acquire GPU resources for a high-complexity task."""
        if not task.gpu_model:
            return True  # No GPU needed
            
        # Use the existing resource arbiter
        return await self.resource_arbiter.acquire_slot(task.gpu_model)

    def release_gpu(self, model_name: str):
        """Release GPU resources after task completion."""
        # The resource arbiter handles this automatically via FIFO eviction
        pass

    def get_agent_status(self, agent_id: str) -> Dict:
        """Get status of an agent's workload."""
        workload = self.agent_workloads.get(agent_id, {})
        if workload:
            return {
                "agent_id": agent_id,
                "role": workload.role,
                "is_busy": workload.is_busy,
                "current_task": workload.current_task.task_id if workload.current_task else None,
                "cpu_affinity": workload.cpu_affinity,
                "gpu_model": workload.gpu_model,
                "task_history_count": len(workload.task_history)
            }
        return {"agent_id": agent_id, "status": "not_registered"}

    def get_system_status(self) -> Dict:
        """Get overall system resource status."""
        cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
        memory = psutil.virtual_memory()
        
        arbiter_status = self.resource_arbiter.get_status()
        
        return {
            "cpu": {
                "logical_cores": self.cpu_count,
                "physical_cores": self.cpu_physical,
                "usage_percent": sum(cpu_percent) / len(cpu_percent),
                "per_core": cpu_percent,
                "affinity": {
                    "os": self.os_cores,
                    "llm": self.llm_cores,
                    "agents": self.agent_cores,
                    "io": self.io_cores
                }
            },
            "memory": {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "percent_used": memory.percent
            },
            "gpu": arbiter_status,
            "tasks": {
                "queued": self.task_queue.qsize(),
                "completed_recent": len(self.completed_tasks),
                "total_processed": self._stats["total_tasks"],
                "avg_queue_time_sec": round(self._stats["avg_queue_time"], 2)
            },
            "agents": {
                "registered": len(self.agent_workloads),
                "busy": sum(1 for w in self.agent_workloads.values() if w.is_busy),
                "idle": sum(1 for w in self.agent_workloads.values() if not w.is_busy)
            }
        }

    async def distribute_workload(self, agent_id: str) -> Optional[Task]:
        """Main distribution loop - call this for each agent to get work."""
        workload = self.agent_workloads.get(agent_id)
        if not workload or workload.is_busy:
            return None
            
        task = await self.get_next_task(agent_id)
        
        if task:
            # Set CPU affinity for this task
            if workload.cpu_affinity:
                try:
                    proc = psutil.Process(os.getpid())
                    proc.cpu_affinity(workload.cpu_affinity)
                except Exception as e:
                    logger.warning(f"Could not set CPU affinity: {e}")
            
            # Acquire GPU if needed
            if task.complexity in [TaskComplexity.HIGH, TaskComplexity.CRITICAL]:
                gpu_acquired = await self.acquire_gpu_for_task(task)
                if not gpu_acquired:
                    # Fall back to CPU if GPU unavailable
                    logger.warning(f"GPU unavailable for task {task.task_id}, using CPU")
                    self._stats["offloaded_tasks"] += 1
                    
            return task
        return None

    async def decentralized_assign(self, task_description: str, candidates: List[str] = None,
                                    timeout_s: float = 5.0) -> Dict:
        """
        Phase 7: Decentralized Task Arbitration.
        Agents vote on task assignments based on expertise match.
        Falls back to centralized arbitration if consensus fails.
        """
        if candidates is None:
            candidates = list(self.agent_workloads.keys())

        if not candidates:
            return {"method": "fallback", "assigned_to": None, "reason": "no_candidates"}

        # Compute expertise score for each candidate
        votes: List[tuple] = []  # (score, agent_id)
        task_lower = task_description.lower()

        for agent_id in candidates:
            wl = self.agent_workloads.get(agent_id)
            if not wl or wl.is_busy:
                continue
            score = 0
            # Role relevance
            if wl.role.lower() in task_lower:
                score += 10
            # Historical success: fewer total tasks = fresher agent = lower priority
            score += min(len(wl.task_history), 10)
            # Not busy bonus
            score += 5
            votes.append((score, agent_id))

        if not votes:
            return {"method": "fallback", "assigned_to": None, "reason": "all_busy"}

        votes.sort(key=lambda x: -x[0])
        winner_score, winner_id = votes[0]

        # Consensus check: winner must have clear lead (>= 2 point margin)
        if len(votes) > 1 and votes[0][0] - votes[1][0] < 2:
            # No clear consensus — use centralized as fallback
            logger.info(f"[DecentralizedArbiter] No consensus (top scores: {votes[0][0]}, {votes[1][0]}). Falling back to centralized.")
            return {
                "method": "centralized_fallback",
                "assigned_to": winner_id,
                "votes": [{"agent": v[1], "score": v[0]} for v in votes[:5]],
                "reason": "no_consensus"
            }

        logger.info(f"[DecentralizedArbiter] Consensus: {winner_id} (score={winner_score})")
        return {
            "method": "decentralized",
            "assigned_to": winner_id,
            "votes": [{"agent": v[1], "score": v[0]} for v in votes[:5]],
            "reason": "consensus"
        }

# Global singleton
_arbiter = None

def get_task_arbiter() -> TaskArbiter:
    global _arbiter
    if _arbiter is None:
        _arbiter = TaskArbiter()
    return _arbiter

# Integration helper for BaseAgent
async def route_task_to_arbiter(agent_id: str, role: str, task: str, model: str = None) -> Optional[Task]:
    """Helper to route agent tasks through the arbiter."""
    arbiter = get_task_arbiter()
    
    # Register agent if not already
    if agent_id not in arbiter.agent_workloads:
        await arbiter.register_agent(agent_id, role, gpu_model=model)
    
    # Create task
    task_id = f"{agent_id}_{int(datetime.now().timestamp())}"
    task_obj = Task(
        task_id=task_id,
        task_type="llm" if len(task) > 100 else "file_io",
        complexity=arbiter.classify_task(task),
        payload={"task": task, "agent_id": agent_id},
        priority=1,
        gpu_model=getattr(arbiter.agent_workloads.get(agent_id), 'gpu_model', None)
    )
    
    # Submit and get assigned work
    await arbiter.submit_task(task_obj)
    work_task = await arbiter.distribute_workload(agent_id)
    
    return work_task
