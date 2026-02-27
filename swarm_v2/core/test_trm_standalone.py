
import sys
import os
import torch

# Ensure we can import from the root
sys.path.append(os.getcwd())

from swarm_v2.core.trm_brain import get_trm_brain

def test_trm():
    print("--- TRM Standalone Test ---")
    try:
        brain = get_trm_brain()
        if brain._model is None:
            print("Failed to initialize TRM model.")
            return

        # Simple test input (dummy tokens within vocab size 12)
        test_input = [1, 2, 3, 4, 5, 0, 0, 0]
        print(f"Input Tokens: {test_input}")
        
        preds = brain.reason(test_input)
        print(f"Reasoning Result (Preds): {preds[:20]}...")
        
        if len(preds) > 0:
            print("✅ TRM Brain functional.")
        else:
            print("❌ TRM Brain returned empty result.")

    except Exception as e:
        print(f"❌ Error during TRM test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_trm()
