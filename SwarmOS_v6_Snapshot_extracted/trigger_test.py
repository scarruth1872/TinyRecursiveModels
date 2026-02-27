
import httpx

url = "http://localhost:8001/swarm/chat"
payload = {
    "role": "Lead Developer",
    "message": "WRITE_FILE: hello_pipeline.py\n```python\ndef hello():\n    return 'Hello Artifact Pipeline!'\n```"
}

try:
    r = httpx.post(url, json=payload, timeout=60)
    print("Response from Lead Developer:")
    print(r.json().get("response"))
except Exception as e:
    print(f"Error: {e}")
