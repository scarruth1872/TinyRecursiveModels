
persona_name = "Archi"
role = "Architect"
background = "Design"
specialties = ["S1", "S2"]
skill_names = ["file_skill"]
action_instructions = "WRITE_FILE: test.py\n```\ncontent\n```"
memory_section = "Memory"

system_prompt = f"""=== IDENTITY ===
You are {persona_name}, an expert AI agent in the Swarm V2 system.
Role: {role}
Background: {background}
Specialties: {', '.join(specialties)}

=== ACTIONS ===
When you need to take action (create files, search, etc.), you MUST emit these EXACT tags:
{action_instructions}

=== RULES ===
1. Rule 1
2. Rule 2

{memory_section}"""

print(f"Original System Prompt:\n{system_prompt}\n")

parts = system_prompt.split("===")
print(f"Parts Count: {len(parts)}")
for i, p in enumerate(parts):
    print(f"Part {i}: '{p}'")

if len(parts) >= 5:
    final_system = "=== IDENTITY ===" + parts[2] + "=== ACTIONS ===" + parts[4]
    print(f"\nFinal System Prompt (Length {len(final_system)}):\n{final_system}")
else:
    print("\nNOT ENOUGH PARTS")
