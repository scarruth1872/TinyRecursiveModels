
import torch
from models.recursive_reasoning.trm import TinyRecursiveReasoningModel_ACTV1

config = {
    "batch_size": 1,
    "seq_len": 1024,
    "num_puzzle_identifiers": 876406,
    "vocab_size": 12,
    "H_cycles": 3,
    "L_cycles": 4,
    "H_layers": 0,
    "L_layers": 2,
    "hidden_size": 512,
    "expansion": 4.0,
    "num_heads": 8,
    "pos_encodings": "rope",
    "halt_max_steps": 16,
    "halt_exploration_prob": 0.1,
    "forward_dtype": "float32",
    "mlp_t": False,
    "puzzle_emb_len": 16,
    "no_ACT_continue": True
}

model = TinyRecursiveReasoningModel_ACTV1(config)
keys = list(model.state_dict().keys())
print("Model keys:")
for k in keys:
    print(k)
