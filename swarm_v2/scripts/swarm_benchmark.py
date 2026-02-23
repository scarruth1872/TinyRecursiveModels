
import asyncio
import time
import json
import os
from datetime import datetime
from swarm_v2.experts.registry import get_expert_team

class SwarmBenchmark:
    def __init__(self):
        self.team = get_expert_team()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "stack_config": "Gemma3-270M + TRM-7M",
            "agent_count": len(self.team),
            "hot_potato": {},
            "consensus_storm": {}
        }

    async def run_hot_potato(self):
        """Sequential handoff across all agents."""
        print("\n--- Starting Mode: Hot Potato (Sequential Latency) ---")
        roles = list(self.team.keys())
        chain_start = time.time()
        
        current_token = "The Potato"
        handoffs = []
        
        for i, role in enumerate(roles):
            agent = self.team[role]
            start = time.time()
            
            # Simple pass-through task
            prompt = f"HOT POTATO: You received '{current_token}'. Pass it to the next role with a 1-sentence comment on your stack health."
            response = await agent.process_task(prompt, sender="Benchmark")
            
            end = time.time()
            latency = end - start
            handoffs.append({"role": role, "latency_sec": round(latency, 2)})
            print(f"[{i+1}/12] {role} processed in {latency:.2f}s")
            
            # Use part of response for next token to ensure real work
            current_token = f"Potato from {role}"

        chain_end = time.time()
        total_time = chain_end - chain_start
        
        self.results["hot_potato"] = {
            "total_time_sec": round(total_time, 2),
            "avg_latency_sec": round(total_time / len(roles), 2),
            "handoffs": handoffs
        }
        print(f"\nHot Potato Results: Total={total_time:.2f}s | Avg={total_time/12:.2f}s per agent")

    async def run_consensus_storm(self):
        """Parallel broadcast to all agents."""
        print("\n--- Starting Mode: Consensus Storm (Parallel Throughput) ---")
        roles = list(self.team.keys())
        storm_start = time.time()
        
        tasks = []
        for role in roles:
            agent = self.team[role]
            tasks.append(agent.process_task("STORM VIBE CHECK: Report your current VRAM estimate and reasoning status in 1 sentence.", sender="Benchmark"))
        
        responses = await asyncio.gather(*tasks)
        storm_end = time.time()
        total_time = storm_end - storm_start
        
        self.results["consensus_storm"] = {
            "total_time_sec": round(total_time, 2),
            "agent_responses": len(responses),
            "throughput_agents_per_sec": round(len(responses) / total_time, 2) if total_time > 0 else 0
        }
        print(f"Consensus Storm Results: All agents responded in {total_time:.2f}s")
        print(f"Throughput: {self.results['consensus_storm']['throughput_agents_per_sec']} agents/sec")

    def save_results(self):
        path = "swarm_v2_artifacts/benchmark_report.json"
        with open(path, "w") as f:
            json.dump(self.results, f, indent=4)
        print(f"\nBenchmark report saved to {path}")

async def main():
    benchmark = SwarmBenchmark()
    await benchmark.run_hot_potato()
    await benchmark.run_consensus_storm()
    benchmark.save_results()

if __name__ == "__main__":
    asyncio.run(main())
