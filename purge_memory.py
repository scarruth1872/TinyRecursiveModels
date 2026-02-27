"""
Memory Purge Script
Removes contaminated task_result entries containing old [BRACKET] label echoes
from all agent memory files. Preserves all clean memory entries.
"""
import json
import os
import glob

MEMORY_DIR = r"f:\Development sites\TRM agent swarm\swarm_v2_memory"
POISON_STRINGS = [
    "[DIRECT NEURAL BRIDGE]",
    "[HMI BRIDGE ACTIVE]",
    "[EXECUTION MODE ACTIVE]",
    "[MESH OBSERVABILITY]",
    "[STRICT CONSTRAINT]",
    "My linguistic output is currently stalled",
    "stalled. Please retry",
    "## CRITICAL: Action Execution Rules\nWhen you need to take action",
    "WRITE_FILE: architecture_overview.md",
    "SEARCH_QUERY: architecture_overview.md",
    "[Archi:Architect] Task:",
    "[PLAN]\nI will outline the steps",
    "[PLAN]\nI will confirm",
]

total_removed = 0
files_cleaned = 0

for filepath in glob.glob(os.path.join(MEMORY_DIR, "*_memory.json")):
    agent = os.path.basename(filepath).replace("_memory.json", "")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[SKIP] {agent}: {e}")
        continue

    # Memory files are flat lists of task entry dicts
    if not isinstance(data, list):
        print(f"[SKIP] {agent}: unexpected structure")
        continue

    original_count = len(data)
    
    # Filter out poisoned entries
    cleaned = []
    removed = []
    for entry in data:
        result = entry.get("result", "") or ""
        task = entry.get("task", "") or ""
        is_poison = any(p in result for p in POISON_STRINGS) or \
                    any(p in task for p in POISON_STRINGS)
        if is_poison:
            removed.append(entry)
        else:
            cleaned.append(entry)

    if removed:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2, ensure_ascii=False)
        print(f"[CLEANED] {agent}: removed {len(removed)} poisoned entries ({original_count} -> {len(cleaned)})")
        total_removed += len(removed)
        files_cleaned += 1
    else:
        print(f"[OK] {agent}: no contamination found ({original_count} entries)")

print(f"\nPurge complete. {total_removed} entries removed across {files_cleaned} files.")
