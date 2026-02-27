
import torch
from models.recursive_reasoning.trm import TinyRecursiveReasoningModel_ACTV1

# Define config based on all_config.yaml and our findings
config = {
    "batch_size": 1,
    "seq_len": 1024, # Most likely for ARC-AGI-1
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
    "forward_dtype": "float32", # Use float32 for CPU compatibility
    "mlp_t": False,
    "puzzle_emb_len": 16,
    "no_ACT_continue": True,
    "puzzle_emb_ndim": 512
}

try:
    model = TinyRecursiveReasoningModel_ACTV1(config)
    state_dict = torch.load("tiny-recursive-weights/step_155718", map_location="cpu")

    # The keys in the checkpoint have '_orig_mod.model.' prefix.
    # We need to strip it to match our model's keys.
    new_state_dict = {}
    for k, v in state_dict.items():
        new_key = k.replace("_orig_mod.model.", "")
        # If we use float32 in model and checkpoint is bfloat16, cast it.
        if v.dtype == torch.bfloat16:
            v = v.to(torch.float32)
        new_state_dict[new_key] = v

    model.load_state_dict(new_state_dict)
    print("✅ Success: TRM 7M Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    import traceback
    traceback.print_exc()
