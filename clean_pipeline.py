
import json
import os

PIPELINE_DB = "f:/Development sites/TRM agent swarm/swarm_v2_memory/artifact_pipeline.json"

if os.path.exists(PIPELINE_DB):
    with open(PIPELINE_DB, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    clean_data = {}
    removed = []
    
    for key, value in data.items():
        if key.endswith('`') or '`' in key:
            removed.append(key)
            continue
        clean_data[key] = value
        
    if removed:
        print(f"Removing malformed keys: {removed}")
        with open(PIPELINE_DB, "w", encoding="utf-8") as f:
            json.dump(clean_data, f, indent=2)
        print("Pipeline database cleaned.")
    else:
        print("No malformed keys found.")
else:
    print("Database not found.")
