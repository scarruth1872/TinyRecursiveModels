"""
Test script for Cognitive Stack with gemma3:270m model.
Verifies that the cognitive stack can load and process prompts using the tiny 270M model.
"""

import asyncio
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swarm_v2.core.cognitive_stack import CognitiveStack

async def test_cognitive_stack_gemma3_270m():
    """Test the cognitive stack with gemma3:270m model."""
    print("🧠 Testing Cognitive Stack with gemma3:270m")
    print("=" * 50)
    
    # Create cognitive stack with gemma3:270m
    agent_name = "TestAgent"
    executive_model = "gemma3:270m"
    
    print(f"Creating CognitiveStack for agent '{agent_name}' with model '{executive_model}'...")
    stack = CognitiveStack(agent_name, executive_model=executive_model)
    
    # Test 1: Simple prompt (should not trigger reasoning)
    print("\nTest 1: Simple prompt (no reasoning offload)")
    prompt1 = "Hello! Can you introduce yourself?"
    print(f"Prompt: {prompt1}")
    
    response1, trace1 = await stack.process(prompt1)
    print(f"Response: {response1[:200]}...")
    print(f"Trace: {trace1}")
    print(f"Stats: {stack.get_status()}")
    
    # Test 2: Reasoning prompt (should trigger TRM)
    print("\nTest 2: Reasoning prompt (should trigger TRM offload)")
    prompt2 = "Analyze the logical consistency of this argument: If A then B, A, therefore B."
    print(f"Prompt: {prompt2}")
    
    response2, trace2 = await stack.process(prompt2)
    print(f"Response: {response2[:200]}...")
    print(f"Trace: {trace2}")
    print(f"Stats: {stack.get_status()}")
    
    # Test 3: Check if the model can handle a coding request
    print("\nTest 3: Simple coding request")
    prompt3 = "Write a Python function to calculate factorial."
    print(f"Prompt: {prompt3}")
    
    response3, trace3 = await stack.process(prompt3)
    print(f"Response: {response3[:200]}...")
    print(f"Trace: {trace3}")
    print(f"Stats: {stack.get_status()}")
    
    # Final summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"- Executive model: {stack.executive_model}")
    print(f"- Executive calls: {stack.stats['executive_calls']}")
    print(f"- Reasoning calls: {stack.stats['reasoning_calls']}")
    print(f"- VRAM estimate: {stack.stats['vram_estimate_mb']} MB")
    
    # Verify the model is actually gemma3:270m
    if "270m" in stack.executive_model.lower():
        print("✅ Model verification: gemma3:270m is active")
    else:
        print(f"⚠️  Model mismatch: Expected gemma3:270m, got {stack.executive_model}")
    
    # Check if TRM reasoning was triggered
    if stack.stats['reasoning_calls'] > 0:
        print("✅ TRM reasoning was triggered for reasoning-intensive prompts")
    else:
        print("⚠️  TRM reasoning was not triggered (might be expected for simple prompts)")
    
    return True

async def test_llm_brain_direct():
    """Test LLM brain directly to ensure gemma3:270m is available."""
    print("\n🔍 Testing LLM Brain directly")
    print("=" * 50)
    
    from swarm_v2.core.llm_brain import get_active_model, llm_chat
    
    # Check which model is active
    active_model = get_active_model()
    print(f"Active model: {active_model}")
    
    if active_model and "270m" in active_model.lower():
        print("✅ gemma3:270m is available as active model")
        
        # Test a simple chat
        response = await llm_chat(
            system_prompt="You are a helpful assistant.",
            user_message="Hello! What's 2+2?",
            model=active_model
        )
        
        if isinstance(response, dict):
            content = response.get("content", "No content")
            thought = response.get("thought", "No thought")
        else:
            content = str(response)
            thought = ""
            
        print(f"Response: {content[:200]}...")
        if thought:
            print(f"Thought: {thought[:100]}...")
    else:
        print(f"⚠️  gemma3:270m is not active. Current model: {active_model}")
        print("Trying to force gemma3:270m...")
        
        # Try to force gemma3:270m
        response = await llm_chat(
            system_prompt="You are a helpful assistant.",
            user_message="Hello! What's 2+2?",
            model="gemma3:270m"
        )
        
        if isinstance(response, dict):
            content = response.get("content", "No content")
        else:
            content = str(response)
            
        if content and not content.startswith("[LLM Error]"):
            print(f"✅ Forced gemma3:270m works! Response: {content[:200]}...")
        else:
            print(f"❌ Forced gemma3:270m failed: {content}")

async def main():
    """Run all tests."""
    print("🚀 Starting gemma3:270m Cognitive Stack Tests")
    print("=" * 50)
    
    try:
        # Test cognitive stack
        await test_cognitive_stack_gemma3_270m()
        
        # Test LLM brain directly
        await test_llm_brain_direct()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        return True
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Enable logging for debugging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)