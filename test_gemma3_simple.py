#!/usr/bin/env python3
"""
Simple test to verify gemma3:270m works with cognitive stack.
"""

import asyncio
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

async def test_cognitive_stack():
    """Test cognitive stack with gemma3:270m."""
    try:
        from swarm_v2.core.cognitive_stack import CognitiveStack
        print("✅ Successfully imported CognitiveStack")
        
        # Create cognitive stack with gemma3:270m
        agent_name = "TestAgent"
        executive_model = "gemma3:270m"
        
        print(f"Creating CognitiveStack with model: {executive_model}")
        stack = CognitiveStack(agent_name, executive_model=executive_model)
        
        print(f"Stack created. Executive model: {stack.executive_model}")
        
        # Test a simple prompt
        prompt = "Hello! What's 2+2?"
        print(f"\nTesting with prompt: {prompt}")
        
        response, trace = await stack.process(prompt)
        print(f"Response: {response[:200]}...")
        print(f"Trace: {trace}")
        
        # Get stats
        stats = stack.get_status()
        print(f"\nStats: {stats}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_llm_brain():
    """Test LLM brain directly."""
    try:
        from swarm_v2.core.llm_brain import get_active_model, llm_chat
        print("\n🔍 Testing LLM brain directly")
        
        active_model = get_active_model()
        print(f"Active model: {active_model}")
        
        # Try gemma3:270m
        response = await llm_chat(
            system_prompt="You are a helpful assistant.",
            user_message="Hello! What's 2+2?",
            model="gemma3:270m"
        )
        
        if isinstance(response, dict):
            content = response.get("content", "No content")
        else:
            content = str(response)
            
        print(f"Response: {content[:200]}...")
        return True
    except Exception as e:
        print(f"LLM brain test error: {e}")
        return False

async def main():
    print("🚀 Testing gemma3:270m with Cognitive Stack")
    print("=" * 50)
    
    success1 = await test_cognitive_stack()
    success2 = await test_llm_brain()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)