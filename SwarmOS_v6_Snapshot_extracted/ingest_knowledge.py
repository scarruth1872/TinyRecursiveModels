
import os
import asyncio
import sys

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

from swarm_v2.skills.learning_engine import get_learning_engine

async def main():
    engine = get_learning_engine()
    skills_root = os.path.join("tmp_repos", "stitch-skills", "skills")
    
    if not os.path.exists(skills_root):
        print(f"Directory not found: {skills_root}")
        return

    print(f"Scanning {skills_root} for skills...")
    
    for category in os.listdir(skills_root):
        category_path = os.path.join(skills_root, category)
        if os.path.isdir(category_path):
            skill_md_path = os.path.join(category_path, "SKILL.md")
            if os.path.exists(skill_md_path):
                print(f"Ingesting skill: {category}...")
                try:
                    # We'll use a simple wrapper to learn from file
                    # We don't have a direct 'learn_from_file' that is easy to call without a persona 
                    # but we can use the engine directly.
                    with open(skill_md_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Manual registration to ensure we get the right name
                    name = f"Skill_{category.replace('-', '_')}"
                    await engine.learn_from_text(
                        name=name,
                        content=content,
                        source=f"stitch-skills/{category}"
                    )
                    print(f"✅ Registered {name}")
                except Exception as e:
                    print(f"❌ Failed to ingest {category}: {e}")

    # Also ingest Jules Awesome List as a general guide
    jules_readme = os.path.join("tmp_repos", "jules-awesome-list", "README.md")
    if os.path.exists(jules_readme):
        print("Ingesting Jules Awesome List...")
        with open(jules_readme, "r", encoding="utf-8") as f:
            content = f.read()
        await engine.learn_from_text(
            name="Skill_Jules_Awesome_Prompts",
            content=content,
            source="jules-awesome-list"
        )
        print("✅ Registered Skill_Jules_Awesome_Prompts")

    print("\nIngestion complete.")
    print(f"Total skills in engine: {len(engine.learned_skills)}")

if __name__ == "__main__":
    asyncio.run(main())
