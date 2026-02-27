
import requests
import json

url = "http://localhost:8001/swarm/chat"
payload = {
    "role": "Lead Developer",
    "message": "Recall the 'Skill_enhance_prompt' from the Neural Skill Registry and explain how you would use it for Stitch optimization. Show me the instructions you recalled."
}

try:
    response = requests.post(url, json=payload)
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
