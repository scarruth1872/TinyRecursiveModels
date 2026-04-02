import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import torch
import uuid
from swarm_manager import SudokuSwarm
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TRM Sudoku Swarm API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static dashboard files
@app.get("/")
async def read_root():
    return FileResponse("index.html")

@app.get("/{path:path}")
async def serve_static(path: str):
    file_path = path
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse("index.html")

swarms = {}

class SwarmConfig(BaseModel):
    num_agents: int = 3
    hidden_size: int = 128
    H_cycles: int = 1
    L_cycles: int = 2

class SudokuTask(BaseModel):
    swarm_id: str
    grid: List[int]
    iterations: int = 5

@app.post("/swarm/create")
async def create_swarm(config: SwarmConfig):
    swarm_id = str(uuid.uuid4())
    
    trm_config = {
        "batch_size": 1,
        "seq_len": 81,
        "num_puzzle_identifiers": 1,
        "puzzle_emb_ndim": 0,
        "puzzle_emb_len": 0,
        "vocab_size": 10,
        "H_cycles": config.H_cycles,
        "L_cycles": config.L_cycles,
        "H_layers": 1,
        "L_layers": 2,
        "hidden_size": config.hidden_size,
        "expansion": 2.0,
        "num_heads": 8,
        "pos_encodings": "none",
        "halt_max_steps": 1,
        "halt_exploration_prob": 0.0,
        "forward_dtype": "float32"
    }
    
    swarm = SudokuSwarm(num_agents=config.num_agents, model_config=trm_config)
    swarms[swarm_id] = {
        "swarm": swarm,
        "config": config
    }
    
    return {"swarm_id": swarm_id, "message": f"Sudoku Swarm with {config.num_agents} agents ready."}

@app.post("/swarm/solve/sudoku")
async def solve_sudoku(task: SudokuTask):
    if task.swarm_id not in swarms:
        raise HTTPException(status_code=404, detail="Swarm not found")
    
    swarm = swarms[task.swarm_id]["swarm"]
    
    if len(task.grid) != 81:
        raise HTTPException(status_code=400, detail="Sudoku grid must contain exactly 81 numbers")

    history = swarm.solve_sudoku(task.grid, max_swarm_steps=task.iterations)
    
    return {
        "swarm_id": task.swarm_id,
        "steps": history,
        "final_grid": [int(torch.tensor(step['probabilities']).argmax(dim=-1)[i]) for step in [history[-1]] for i in range(81)]
    }

@app.get("/health")
async def health():
    return {"status": "online"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
