
import requests
import json

API_BASE = "http://localhost:8000"

KNOWLEDGE_PACKS = [
    {
        "name": "FastAPI_Production_Hardening",
        "content": """
Best practices for securing and scaling FastAPI for AI Agent deployments.
1. Middleware: Implement CORS policies, HSTS, CSP, and X-Frame-Options. Use rate-limiting to prevent DoS.
2. Background Tasks: For simple operations, use 'BackgroundTasks'. For long-running or critical tasks, use Celery/ARQ with Redis.
3. Security: Use OAuth2/JWT for sessions. Disable Swagger UI in production. Never hardcode secrets; use env variables.
4. Input Validation: Use Pydantic models for strict schema enforcement. Sanitize data to prevent injection.
5. Async Execution: Use timeouts and retries for external agent tool calls to prevent event loop blocking.
6. Structured Output: Define and validate agent JSON responses to ensure integration reliability.
        """,
        "source": "Search_Analysis"
    },
    {
        "name": "Vector_Intelligence_ChromaDB",
        "content": """
Advanced memory management using ChromaDB for Agent Collective Consciousness.
1. Persist Directory: Always initialize with a dedicated 'persist_directory' to ensure memory survives restarts.
2. Embedding Selection: Use high-dimension models like 'all-MiniLM-L6-v2' or Gemini embeddings for better semantic retrieval.
3. Metadata Filtering: Store agent_role, task_id, and timestamp in metadata to allow targeted memory queries.
4. Efficient Retrieval: Use 'n_results' to limit LLM context windows and prevent token overflows.
5. Collection Management: Separate 'system_knowledge' from 'session_conversations' to maintain high signal-to-noise ratio.
        """,
        "source": "Vector_DB_Best_Practices"
    }
]

def ingest():
    print("🚀 Initializing Second Phase of Knowledge Ingestion...")
    for pack in KNOWLEDGE_PACKS:
        print(f"Ingesting: {pack['name']}...")
        try:
            resp = requests.post(f"{API_BASE}/learning/ingest", json=pack)
            if resp.status_code == 200:
                print(f"✅ Successfully ingested {pack['name']}")
                print(f"   Status: {resp.json().get('status')}")
            else:
                print(f"❌ Failed to ingest {pack['name']}: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"⚠️ Error connecting to API: {e}")

if __name__ == "__main__":
    ingest()
