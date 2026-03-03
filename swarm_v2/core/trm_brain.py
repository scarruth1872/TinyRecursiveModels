
import os
import torch
import torch.nn as nn
from typing import Dict, Any, Optional, List
from models.recursive_reasoning.trm import TinyRecursiveReasoningModel_ACTV1

class TRMBrain:
    _instance = None
    _model = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TRMBrain, cls).__new__(cls)
        return cls._instance

    def __init__(self, checkpoint_path: str = "tiny-recursive-weights/step_155718"):
        if self._model is not None:
            return

        self.checkpoint_path = checkpoint_path
        self.config = {
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
            "no_ACT_continue": True,
            "puzzle_emb_ndim": 512
        }
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[TRM Brain] Initializing on {self.device}...")
        
        try:
            self._model = TinyRecursiveReasoningModel_ACTV1(self.config)
            
            if os.path.exists(self.checkpoint_path):
                state_dict = torch.load(self.checkpoint_path, map_location=self.device)
                
                # Strip prefix
                new_state_dict = {}
                for k, v in state_dict.items():
                    new_key = k.replace("_orig_mod.model.", "")
                    if v.dtype == torch.bfloat16 and self.device == torch.device("cpu"):
                         v = v.to(torch.float32)
                    new_state_dict[new_key] = v
                
                self._model.load_state_dict(new_state_dict)
                self._model.to(self.device).eval()
                print(f"[TRM Brain] Model loaded from {self.checkpoint_path}")
            else:
                print(f"[TRM Brain] Warning: Checkpoint not found at {self.checkpoint_path}")
        except Exception as e:
            print(f"[TRM Brain] Failed to load model: {e}")
            self._model = None

    def reason(self, input_tokens: List[int], puzzle_id: int = 0) -> List[int]:
        """
        Perform recursive reasoning on a sequence of tokens.
        """
        if self._model is None:
            print("[TRM Brain] Error: Model not loaded.")
            return []

        with torch.no_grad():
            inputs = torch.tensor(input_tokens).unsqueeze(0).to(self.device)
            p_id = torch.tensor([puzzle_id]).to(self.device)
            
            # Check seq_len match
            if inputs.shape[1] < self.config['seq_len']:
                padding = torch.zeros((1, self.config['seq_len'] - inputs.shape[1]), dtype=torch.long).to(self.device)
                inputs = torch.cat([inputs, padding], dim=1)
            else:
                inputs = inputs[:, :self.config['seq_len']]

            batch = {
                "inputs": inputs,
                "puzzle_identifiers": p_id
            }

            carry = self._model.initial_carry(batch)
            
            # Loop for dynamic H_cycles to achieve deep reasoning logic
            total_preds = []
            h_cycles = kwargs.get("h_cycles", self.config['H_cycles'])
            
            for _ in range(h_cycles):
                carry, outputs = self._model(carry, batch)
                logits = outputs["logits"] # [1, seq_len, vocab_size]
                # Extract the reasoning token predictions
                preds = torch.argmax(logits, dim=-1).squeeze(0).cpu().tolist()
                total_preds.extend(preds[:12]) # Take sequence snippet per cycle
                
            return total_preds

def get_trm_brain():
    return TRMBrain()
