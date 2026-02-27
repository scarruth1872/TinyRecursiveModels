
from swarm_v2.experts.registry import get_expert_team
team = get_expert_team()
archi = team.get("Architect")
if archi:
    print(f"Name: {archi.persona.name}")
    print(f"Role: {archi.persona.role}")
    skill_names = [getattr(s, "skill_name", s.__class__.__name__) for s in archi.skills]
    print(f"Skills: {skill_names}")
    has_call = any(hasattr(s, "call_tool") for s in archi.skills)
    print(f"Has call_tool: {has_call}")
else:
    print("Architect not found in team")
