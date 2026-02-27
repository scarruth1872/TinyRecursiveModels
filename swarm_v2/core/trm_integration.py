"""
TRM Integration - Connects TRM Orchestrator with BaseAgent System

Provides:
1. Enhanced BaseAgent with TRM recursive reasoning capabilities
2. Integration with existing skill system
3. Performance monitoring and optimization
4. LLM synthesis for final output
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from swarm_v2.core.trm_orchestrator import get_trm_orchestrator, TRMOrchestrator
from swarm_v2.core.base_agent import BaseAgent, AgentPersona
from swarm_v2.core.task_arbiter import get_task_arbiter, ComputeTarget, TaskComplexity
from swarm_v2.core.llm_brain import llm_chat, build_system_prompt

class TRMEnhancedAgent(BaseAgent):
    """
    BaseAgent enhanced with TRM recursive reasoning capabilities.
    
    Extends BaseAgent with:
    - Parallel sub-agent spawning via TRM
    - Stateful superposition for competing interpretations
    - Resource-aware task distribution
    - LLM synthesis for final output
    """
    
    def __init__(self, persona: AgentPersona, skills: List[Any] = None):
        super().__init__(persona, skills)
        self.trm_orchestrator = get_trm_orchestrator(self)
        self.parallel_enabled = True
        self.max_recursion_depth = 3
        self.confidence_threshold = 0.75
        
        # Performance tracking
        self.trm_metrics = {
            "total_trm_tasks": 0,
            "parallel_executions": 0,
            "avg_speedup": 1.0,
            "resource_utilization": {},
            "error_reduction": 0.0
        }
        
    async def process_with_trm(self, task: str, sender: str = "user") -> Dict[str, Any]:
        """
        Process task using TRM-enhanced parallel reasoning.
        
        Steps:
        1. Analyze task complexity
        2. Partition context for parallel processing
        3. Spawn sub-agents for parallel reasoning
        4. Aggregate results with superposition
        5. Synthesize final output with LLM
        """
        self.log_nodal_activity(f"Starting TRM-enhanced processing: {task[:60]}")
        
        # Measure baseline performance
        start_time = time.time()
        
        # Step 1: Analyze task complexity
        complexity = self._analyze_task_complexity(task)
        self.log_nodal_activity(f"Task complexity: {complexity}")
        
        # Step 2: Determine if parallel processing is beneficial
        should_parallel = self._should_use_parallel(complexity, task)
        if not should_parallel or not self.parallel_enabled:
            self.log_nodal_activity("Using sequential processing")
            return await self._process_sequential(task, sender)
            
        # Step 3: Partition context
        partitions = self.trm_orchestrator.partition_context(task, self.trm_orchestrator.max_parallel_tasks)
        self.log_nodal_activity(f"Partitioned into {len(partitions)} sub-tasks")
        
        # Step 4: Execute parallel reasoning
        parallel_results = await self._execute_parallel_reasoning(partitions, complexity)
        
        # Step 5: Aggregate and synthesize
        final_result = await self._synthesize_results(parallel_results, task, sender)
        
        # Step 6: Update metrics
        self._update_trm_metrics(start_time, len(partitions), parallel_results)
        
        return final_result
        
    async def _execute_parallel_reasoning(self, 
                                        partitions: List[str],
                                        complexity: str) -> List[Dict[str, Any]]:
        """Execute reasoning tasks in parallel using TRM orchestrator."""
        self.log_nodal_activity(f"Starting parallel reasoning with {len(partitions)} partitions")
        
        # Create sub-tasks
        sub_tasks = []
        for i, partition in enumerate(partitions):
            sub_task = {
                "id": f"{self.agent_id}_{i}_{int(time.time())}",
                "context": partition,
                "complexity": complexity,
                "partition_idx": i
            }
            sub_tasks.append(sub_task)
            
        # Use TRM orchestrator for parallel execution
        results = []
        if len(sub_tasks) > 1 and self.parallel_enabled:
            # Batch execution via orchestrator
            batch_results = await self.trm_orchestrator.spawn_sub_reasoning(
                context="\n".join(partitions),
                depth=0,
                max_depth=self.max_recursion_depth,
                confidence_threshold=self.confidence_threshold
            )
            
            if batch_results.get("status") == "collapsed":
                # Successful parallel execution
                result = batch_results["result"]
                results.append({
                    "type": "parallel_batch",
                    "result": result,
                    "parallel_tasks": batch_results.get("parallel_tasks", 1),
                    "depth": batch_results.get("depth", 0)
                })
            else:
                # Fall back to sequential per partition
                self.log_nodal_activity("Parallel batch failed, falling back to per-partition")
                for sub_task in sub_tasks:
                    partition_result = await self._process_partition(sub_task)
                    results.append(partition_result)
        else:
            # Sequential execution
            for sub_task in sub_tasks:
                partition_result = await self._process_partition(sub_task)
                results.append(partition_result)
                
        return results
        
    async def _process_partition(self, sub_task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single partition."""
        start_time = time.time()
        
        try:
            # Use TRM for symbolic reasoning, LLM for text
            if self._looks_like_symbolic(sub_task["context"]):
                # Use TRM brain directly
                from swarm_v2.core.trm_brain import get_trm_brain
                trm_brain = get_trm_brain()
                
                # Convert to tokens
                tokens = []
                for part in sub_task["context"].split():
                    try:
                        tokens.append(int(part))
                    except ValueError:
                        tokens.append(abs(hash(part)) % 10)
                        
                result_tokens = trm_brain.reason(tokens)
                
                result = {
                    "type": "symbolic",
                    "tokens": result_tokens[:len(tokens)],
                    "original_tokens": tokens,
                    "processing_time": time.time() - start_time
                }
            else:
                # Use LLM for text processing
                prompt = f"Analyze this text partition: {sub_task['context']}"
                response = await self._llm_generate(prompt)
                
                result = {
                    "type": "text",
                    "content": response,
                    "original": sub_task["context"],
                    "processing_time": time.time() - start_time
                }
                
            result["task_id"] = sub_task["id"]
            result["success"] = True
            
        except Exception as e:
            result = {
                "type": "error",
                "error": str(e),
                "task_id": sub_task["id"],
                "processing_time": time.time() - start_time,
                "success": False
            }
            
        return result
        
    async def _synthesize_results(self, 
                                results: List[Dict[str, Any]],
                                original_task: str,
                                sender: str) -> Dict[str, Any]:
        """Synthesize parallel results into final output."""
        self.log_nodal_activity(f"Synthesizing {len(results)} results")
        
        # Prepare synthesis context
        synthesis_context = self._prepare_synthesis_context(results, original_task)
        
        # Use LLM for final synthesis
        synthesis_prompt = self._build_synthesis_prompt(synthesis_context, original_task)
        
        try:
            final_response = await self._llm_generate(synthesis_prompt)
            
            # Extract any action tags
            final_response = await self._execute_action_tags(final_response)
            
            # Build comprehensive result
            comprehensive_result = {
                "response": final_response,
                "processing_mode": "parallel" if len(results) > 1 else "sequential",
                "partition_count": len(results),
                "synthesis_quality": self._evaluate_synthesis_quality(results, final_response),
                "trm_metrics": self.trm_metrics.copy()
            }
            
            # Add detailed results if verbose
            if any(r.get("type") == "symbolic" for r in results):
                comprehensive_result["symbolic_processing"] = True
                
            self.log_nodal_activity("Synthesis complete")
            return comprehensive_result
            
        except Exception as e:
            self.log_nodal_activity(f"Synthesis failed: {str(e)}")
            # Fall back to simple aggregation
            return self._fallback_aggregation(results, original_task)
            
    def _prepare_synthesis_context(self, results: List[Dict[str, Any]], original_task: str) -> str:
        """Prepare context for LLM synthesis."""
        context_parts = []
        context_parts.append(f"Original Task: {original_task}")
        context_parts.append(f"Number of parallel analyses: {len(results)}")
        context_parts.append("")
        
        for i, result in enumerate(results):
            if result.get("success", False):
                result_type = result.get("type", "unknown")
                if result_type == "symbolic":
                    tokens = result.get("tokens", [])
                    original = result.get("original_tokens", [])
                    context_parts.append(f"Analysis {i+1} (Symbolic):")
                    context_parts.append(f"  Original: {original[:20]}...")
                    context_parts.append(f"  Result: {tokens[:20]}...")
                elif result_type == "text":
                    content = result.get("content", "")
                    context_parts.append(f"Analysis {i+1} (Text):")
                    context_parts.append(f"  {content[:200]}...")
                elif result_type == "parallel_batch":
                    batch_result = result.get("result", {})
                    confidence = batch_result.get("confidence", 0)
                    context_parts.append(f"Analysis {i+1} (Parallel Batch):")
                    context_parts.append(f"  Confidence: {confidence:.2f}")
                    context_parts.append(f"  Interpretations: {batch_result.get('alternative_count', 1)}")
            else:
                context_parts.append(f"Analysis {i+1} (Failed): {result.get('error', 'Unknown error')}")
                
            context_parts.append(f"  Processing time: {result.get('processing_time', 0):.2f}s")
            context_parts.append("")
            
        return "\n".join(context_parts)
        
    def _build_synthesis_prompt(self, context: str, original_task: str) -> str:
        """Build prompt for LLM synthesis."""
        return f"""You are synthesizing results from parallel reasoning tasks.

{context}

Based on these parallel analyses, provide a comprehensive response to the original task.

Original task: {original_task}

Guidelines:
1. Consider all analyses, even conflicting ones
2. Note any patterns or consensus across analyses
3. Highlight uncertainties or areas needing clarification
4. Provide the most likely correct answer based on the evidence
5. If symbolic patterns were analyzed, explain their meaning

Provide your synthesis below:"""
        
    async def _process_sequential(self, task: str, sender: str) -> Dict[str, Any]:
        """Process task sequentially (fallback)."""
        self.log_nodal_activity("Using sequential processing")
        
        # Use parent class processing
        response = await super().process_task(task, sender)
        
        return {
            "response": response,
            "processing_mode": "sequential",
            "partition_count": 1,
            "synthesis_quality": 1.0,  # No synthesis needed
            "trm_metrics": self.trm_metrics.copy()
        }
        
    def _analyze_task_complexity(self, task: str) -> str:
        """Analyze task complexity for parallel processing decisions."""
        task_lower = task.lower()
        
        # High complexity indicators
        high_complexity_keywords = [
            "analyze", "compare", "evaluate", "explain", "interpret",
            "solve", "calculate", "reason", "deduce", "infer"
        ]
        
        # Symbolic processing indicators
        symbolic_keywords = [
            "pattern", "sequence", "tokens", "symbol", "logic",
            "puzzle", "riddle", "algorithm", "formula"
        ]
        
        high_complexity = any(kw in task_lower for kw in high_complexity_keywords)
        symbolic = any(kw in task_lower for kw in symbolic_keywords)
        
        if symbolic:
            return "symbolic_high"
        elif high_complexity and len(task) > 200:
            return "text_high"
        elif len(task) > 500:
            return "text_medium"
        else:
            return "text_low"
            
    def _should_use_parallel(self, complexity: str, task: str) -> bool:
        """Determine if parallel processing is beneficial."""
        if not self.parallel_enabled:
            return False
            
        # Check system resources
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        if cpu_percent > 80 or memory.percent > 85:
            self.log_nodal_activity("System resources constrained, using sequential")
            return False
            
        # Complexity-based decision
        if complexity in ["symbolic_high", "text_high"]:
            return len(task) > 100  # Long complex tasks benefit from parallel
            
        if complexity == "text_medium":
            return len(task) > 300  # Medium tasks benefit if long enough
            
        return False  # Simple tasks don't need parallel
        
    def _looks_like_symbolic(self, text: str) -> bool:
        """Check if text looks like symbolic tokens."""
        if not text:
            return False
            
        # Count numeric and separator characters
        symbolic_chars = 0
        total_chars = len(text)
        
        for char in text:
            if char.isdigit() or char.isspace() or char in ",.;:|":
                symbolic_chars += 1
                
        return symbolic_chars / total_chars > 0.6
        
    def _evaluate_synthesis_quality(self, results: List[Dict[str, Any]], final_response: str) -> float:
        """Evaluate quality of synthesis (0.0 to 1.0)."""
        if not results:
            return 0.0
            
        # Simple heuristic based on success rate and response length
        successful = sum(1 for r in results if r.get("success", False))
        success_rate = successful / len(results)
        
        # Check if response seems comprehensive
        response_length = len(final_response)
        comprehensive = min(1.0, response_length / 1000)  # Normalize
        
        # Weighted average
        quality = (success_rate * 0.7) + (comprehensive * 0.3)
        return min(1.0, max(0.0, quality))
        
    def _fallback_aggregation(self, results: List[Dict[str, Any]], original_task: str) -> Dict[str, Any]:
        """Fallback aggregation when synthesis fails."""
        successful_results = [r for r in results if r.get("success", False)]
        
        if not successful_results:
            return {
                "response": "All parallel analyses failed. Please try sequential processing.",
                "processing_mode": "parallel_failed",
                "partition_count": len(results),
                "successful_partitions": 0,
                "trm_metrics": self.trm_metrics.copy()
            }
            
        # Simple concatenation
        aggregated = []
        for result in successful_results:
            if result.get("type") == "text":
                aggregated.append(result.get("content", ""))
            elif result.get("type") == "symbolic":
                tokens = result.get("tokens", [])
                aggregated.append(f"Symbolic result: {tokens[:10]}...")
                
        response = "\n\n".join(aggregated)
        
        return {
            "response": f"Aggregated results:\n\n{response}",
            "processing_mode": "parallel_aggregated",
            "partition_count": len(results),
            "successful_partitions": len(successful_results),
            "trm_metrics": self.trm_metrics.copy()
        }
        
    def _update_trm_metrics(self, start_time: float, partition_count: int, results: List[Dict[str, Any]]):
        """Update TRM performance metrics."""
        total_time = time.time() - start_time
        
        # Calculate speedup (estimated)
        estimated_sequential_time = total_time * partition_count * 0.7  # Rough estimate
        if estimated_sequential_time > 0:
            speedup = estimated_sequential_time / total_time
        else:
            speedup = 1.0
            
        # Update running averages
        self.trm_metrics["total_trm_tasks"] += 1
        self.trm_metrics["parallel_executions"] += 1 if partition_count > 1 else 0
        self.trm_metrics["avg_speedup"] = (self.trm_metrics["avg_speedup"] * 0.9 + 
                                          speedup * 0.1)
                                          
        # Track successful partitions
        successful = sum(1 for r in results if r.get("success", False))
        if partition_count > 0:
            success_rate = successful / partition_count
            error_reduction = 1.0 - (1.0 - success_rate)  # Simple metric
            self.trm_metrics["error_reduction"] = (self.trm_metrics["error_reduction"] * 0.9 + 
                                                  error_reduction * 0.1)
        
    def get_trm_status(self) -> Dict[str, Any]:
        """Get TRM enhancement status."""
        orchestrator_status = self.trm_orchestrator.get_status()
        
        return {
            "agent_id": self.agent_id,
            "parallel_enabled": self.parallel_enabled,
            "max_recursion_depth": self.max_recursion_depth,
            "confidence_threshold": self.confidence_threshold,
            "trm_metrics": self.trm_metrics.copy(),
            "orchestrator_status": orchestrator_status
        }
        
    def enable_parallel(self, enabled: bool = True):
        """Enable or disable parallel processing."""
        self.parallel_enabled = enabled
        self.log_nodal_activity(f"Parallel processing {'enabled' if enabled else 'disabled'}")
        
    def set_recursion_depth(self, depth: int):
        """Set maximum recursion depth."""
        self.max_recursion_depth = max(1, min(5, depth))  # Limit to 1-5
        self.log_nodal_activity(f"Recursion depth set to {self.max_recursion_depth}")


# Factory function for creating TRM-enhanced agents
def create_trm_enhanced_agent(persona: AgentPersona, skills: List[Any] = None) -> TRMEnhancedAgent:
    """Create a TRM-enhanced agent with parallel reasoning capabilities."""
    return TRMEnhancedAgent(persona, skills)


# Integration helper for existing system
def enhance_existing_agent(base_agent: BaseAgent) -> TRMEnhancedAgent:
    """Enhance an existing BaseAgent with TRM capabilities."""
    # Create enhanced version with same persona and skills
    enhanced = TRMEnhancedAgent(
        persona=base_agent.persona,
        skills=list(base_agent.skills)
    )
    
    # Copy relevant state
    enhanced.memory = base_agent.memory
    enhanced.subagents = base_agent.subagents
    enhanced.nodal_logs = base_agent.nodal_logs
    
    return enhanced