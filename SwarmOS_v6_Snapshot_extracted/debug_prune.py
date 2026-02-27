
import os
import json
from datetime import datetime

ARTIFACTS_DIR = "swarm_v2_artifacts"
PIPELINE_DB = "swarm_v2_memory/artifact_pipeline.json"

def test_prune():
    with open(PIPELINE_DB, "r") as f:
        artifacts = json.load(f)
    
    now = datetime.now()
    count = 0
    for rel_path, meta in list(artifacts.items()):
        if rel_path.startswith("test_"):
            created_at = meta.get("created_at")
            if created_at:
                dt = datetime.fromisoformat(created_at)
                hours_old = (now - dt).total_seconds() / 3600
                print(f"File: {rel_path}, Hours Old: {hours_old}")
                if hours_old > 1:
                    print(f"  -> Should delete {rel_path}")
                    count += 1
    print(f"Total to delete: {count}")

test_prune()
