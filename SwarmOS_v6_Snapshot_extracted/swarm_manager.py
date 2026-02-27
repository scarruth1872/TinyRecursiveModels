
import os
import torch
import torch.nn as nn
from typing import List, Dict, Any, Optional
from models.recursive_reasoning.trm import TinyRecursiveReasoningModel_ACTV1

class TRMAgent:
    def __init__(self, agent_id: str, model_config: dict, seed: int = 0):
        self.agent_id = agent_id
        torch.manual_seed(seed)
        self.model = TinyRecursiveReasoningModel_ACTV1(model_config)
        self.model.eval()
        self.carry = None

    def initialize_task(self, batch: Dict[str, torch.Tensor]):
        self.carry = self.model.initial_carry(batch)

    def step(self, batch: Dict[str, torch.Tensor]):
        if self.carry is None:
            self.initialize_task(batch)
        
        # We want to capture logits before and after consensus
        self.carry, outputs = self.model(self.carry, batch)
        return outputs

    def get_latent_state(self):
        if self.carry:
            return self.carry.inner_carry.z_H.clone(), self.carry.inner_carry.z_L.clone()
        return None, None

    def set_latent_state(self, z_H: torch.Tensor, z_L: torch.Tensor):
        if self.carry:
            self.carry.inner_carry.z_H = z_H
            self.carry.inner_carry.z_L = z_L

class SudokuSwarm:
    def __init__(self, num_agents: int, model_config: dict):
        self.agents = [TRMAgent(f"Agent-{i}", model_config, seed=i*100) for i in range(num_agents)]
        self.config = model_config

    def solve_sudoku(self, grid: List[int], max_swarm_steps: int = 10):
        # Convert flat list (81 numbers) to tensor
        # Sudoku usually has vocab 10 (0 for blank, 1-9 for digits)
        inputs = torch.tensor(grid).view(1, -1) # [1, 81]
        
        # Pad or trim to match seq_len
        if inputs.shape[1] < self.config['seq_len']:
            inputs = torch.cat([inputs, torch.zeros((1, self.config['seq_len'] - inputs.shape[1]), dtype=torch.long)], dim=1)
        else:
            inputs = inputs[:, :self.config['seq_len']]

        mock_batch = {
            "inputs": inputs,
            "puzzle_identifiers": torch.tensor([0])
        }

        # Initialize all agents
        for agent in self.agents:
            agent.initialize_task(mock_batch)

        history = []

        for s in range(max_swarm_steps):
            agent_logits = []
            all_z_H = []
            all_z_L = []

            for agent in self.agents:
                outputs = agent.step(mock_batch)
                agent_logits.append(outputs["logits"])
                z_H, z_L = agent.get_latent_state()
                all_z_H.append(z_H)
                all_z_L.append(z_L)

            # Consensus logic: Average latent states (Recursive Swarm Intelligence)
            mean_z_H = torch.stack(all_z_H).mean(dim=0)
            mean_z_L = torch.stack(all_z_L).mean(dim=0)

            # Update agents
            for agent in self.agents:
                agent.set_latent_state(mean_z_H, mean_z_L)

            # Calculate consensus logits (distribution over the grid)
            avg_logits = torch.stack(agent_logits).mean(dim=0)
            probs = torch.softmax(avg_logits, dim=-1)
            
            # Record per-step state for visualization
            step_results = {
                "step": s,
                "probabilities": probs[0, :81].detach().cpu().numpy().tolist(), # [81, 10]
                "confidence": float(probs.max().item())
            }
            history.append(step_results)

        return history

if __name__ == "__main__":
    # Test with Sudoku-like config
    cfg = {
        "batch_size": 1,
        "seq_len": 81,
        "num_puzzle_identifiers": 1,
        "puzzle_emb_ndim": 0,
        "puzzle_emb_len": 0,
        "vocab_size": 10,
        "H_cycles": 1,
        "L_cycles": 1,
        "H_layers": 1,
        "L_layers": 1,
        "hidden_size": 64,
        "expansion": 2.0,
        "num_heads": 4,
        "pos_encodings": "none",
        "halt_max_steps": 1,
        "halt_exploration_prob": 0.0,
        "forward_dtype": "float32"
    }
    swarm = SudokuSwarm(3, cfg)
    mock_grid = [0]*81
    mock_grid[0] = 5 # Clue
    res = swarm.solve_sudoku(mock_grid, max_swarm_steps=2)
    print(f"Swarm processed {len(res)} steps. Step 0 confidence: {res[0]['confidence']}")
