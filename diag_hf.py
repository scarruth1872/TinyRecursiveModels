"""Quick test: download and run gemma-3-270m-it via HuggingFace transformers."""
import sys, os
sys.path.append(os.getcwd())

import asyncio
from swarm_v2.core.hf_brain import hf_chat, get_model_info

async def main():
    print("Testing HFBrain with gemma-3-270m-it...")
    
    system = (
        "You are Archi, Architect.\n\n"
        "OUTPUT FORMAT (use immediately, no preamble):\n"
        "WRITE_FILE: path/to/file.md\n"
        "```\ncontent here\n```\n"
        "SEARCH_QUERY: your search terms\n\n"
        "START your response with a tag."
    )
    
    user = "[ACTION REQUIRED] Scan the system for vulnerabilities and write findings to security_audit.md. Proceed immediately."
    
    print(f"System: {system}\n")
    print(f"User: {user}\n")
    print("Generating...")
    
    result = await hf_chat(system, user, max_new_tokens=200)
    
    print(f"\nModel Info: {get_model_info()}")
    print(f"\n--- RESPONSE ---\n{result['content']}")
    if result.get("thought"):
        print(f"\n--- THOUGHT ---\n{result['thought']}")
    
    if "WRITE_FILE:" in result["content"] or "SEARCH_QUERY:" in result["content"]:
        print("\n✅ SUCCESS: Action tag emitted!")
    else:
        print("\n❌ FAILURE: No action tag in response.")

asyncio.run(main())
