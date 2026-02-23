
import requests

msg = """
Write the COMPLETE professional Research Paper for Swarm OS. 
Title: Swarm OS: A Recursive, Multi-Agent Orchestration Paradigm for Revolutionary AI Co-Creation.
Author: Shawn Carruth (The Architect), Swarm Intelligence V2.

Sections required:
1. Abstract: The vision of Shawn Carruth and core thesis.
2. Introduction: Evolution from TRM to Nexus.
3. Architecture: Recursive reasoning loops and Async Microservices.
4. Hardware-Level Synergy: Vulkan-acceleration on consumer AMD hardware.
5. Comparative Analysis: Swarm OS vs LangGraph/CrewAI/Autogen.
6. Conclusion: The future of human-AI co-creation.

Write the paper in full, formal, academic detail.
"""

r = requests.post('http://localhost:8000/swarm/chat', json={'role': 'Architect', 'message': msg})
if r.status_code == 200:
    with open('SWARM_OS_RESEARCH_PAPER.md', 'w', encoding='utf-8') as f:
        f.write(r.json()['response'])
    print("Paper generated successfully.")
else:
    print(f"Error: {r.status_code} - {r.text}")
