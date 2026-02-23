
import os

SYNTH_DIR = "swarm_v2_synthesized"

def fix_files():
    if not os.path.exists(SYNTH_DIR):
        print(f"Directory {SYNTH_DIR} not found.")
        return

    fixed_count = 0
    for filename in os.listdir(SYNTH_DIR):
        if filename.endswith(".py"):
            path = os.path.join(SYNTH_DIR, filename)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Fix backslashes in source paths
            # Patterns: "source": "file://...\" -> "source": "file://.../"
            # We can just replace swarm_v2_artifacts\seed_docs\ with swarm_v2_artifacts/seed_docs/
            
            new_content = content.replace("swarm_v2_artifacts\\seed_docs\\", "swarm_v2_artifacts/seed_docs/")
            
            # Also catch duplicate closing brackets if I messed up any manual edits
            new_content = new_content.replace("}\n        ],\n        ]", "}\n        ]") 

            if new_content != content:
                print(f"Fixing {filename}...")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                fixed_count += 1
    
    print(f"Fixed {fixed_count} files.")

if __name__ == "__main__":
    fix_files()
