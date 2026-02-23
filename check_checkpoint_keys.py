
import torch

checkpoint_path = "tiny-recursive-weights/step_155718"
state_dict = torch.load(checkpoint_path, map_location="cpu")

print("First 10 keys:")
for k in list(state_dict.keys())[:10]:
    print(k)

print("\nTotal keys:", len(state_dict))
