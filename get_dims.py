
import torch

checkpoint_path = "tiny-recursive-weights/step_155718"
state_dict = torch.load(checkpoint_path, map_location="cpu")

weight = state_dict["_orig_mod.model.inner.embed_tokens.embedding_weight"]
print(f"Vocab size: {weight.shape[0]}")
print(f"Hidden size: {weight.shape[1]}")

puzzle_weight = state_dict["_orig_mod.model.inner.puzzle_emb.weights"]
print(f"Num puzzles: {puzzle_weight.shape[0]}")
