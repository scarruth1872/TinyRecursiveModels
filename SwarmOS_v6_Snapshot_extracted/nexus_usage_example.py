
"""
Nexus Platform: Usage Example
Demonstrates how to use the Nexus components as a Python module.
"""
from swarm_v2_integrated.agent_manager import agents
from swarm_v2_integrated.task_router import TaskRouter

def run_local_demo():
    print("--- Nexus Local Module Demo ---")
    
    # 1. Initialize Task Router
    router = TaskRouter()
    
    # 2. Register Agents
    router.register_agent("Archi-01", ["system-design", "architecture"], 100)
    router.register_agent("Devo-01", ["python", "fastapi"], 100)
    router.register_agent("Shield-01", ["security", "audit"], 100)
    
    # 3. Create a Task
    task = {
        "id": "T-999",
        "description": "Design a secure microservice",
        "required_skills": ["system-design"]
    }
    
    # 4. Analyze and Dispatch
    print(f"\nAnalyzing Task: {task['description']}")
    assigned_agent = router.analyze_task(task)
    
    if assigned_agent:
        print(f"Success! Task assigned to: {assigned_agent}")
        router.distribute_task(task, assigned_agent)
    else:
        print("No agent found with the required skills.")
        
    # 5. Show Queue
    print(f"\nCurrent Task Queue: {router.get_task_queue()}")

if __name__ == "__main__":
    run_local_demo()
