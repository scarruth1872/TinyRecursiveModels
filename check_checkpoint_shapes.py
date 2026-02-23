
import torch

checkpoint_path = "tiny-recursive-weights/step_155718"
state_dict = torch.load(checkpoint_path, map_location="cpu")

for k in ["_orig_mod.model.inner.embed_tokens.embedding_weight", "_orig_mod.model.inner.puzzle_emb.weights"]:
    if k in state_dict:
        print(f"{k} shape: {state_dict[k].shape}")
