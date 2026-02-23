
import os
import requests
import json
from typing import Optional, List

from dotenv import load_dotenv

# Load .env at the source-level to ensure key is available to all instances
load_dotenv()

# Try to get API key from environment, default to None (will return simulated results)
# In production, set TAVILY_API_KEY environment variable.
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

class WebSearchSkill:
    """
    Web Search Skill for Swarm V2.
    Integrates with Tavily AI for high-quality, LLM-optimized search results.
    Fallbacks to a simulated mode if no API key is present.
    """
    skill_name = "WebSearchSkill"
    description = "Search the real-time web for information, documentation, and data."

    def __init__(self, api_key: str = None):
        self.api_key = api_key or TAVILY_API_KEY

    def search(self, query: str, max_results: int = 5) -> str:
        """Perform a web search."""
        if not self.api_key:
            return self._simulated_search(query)

        try:
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": max_results,
                "include_answer": True
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self._format_results(data)
            else:
                return f"❌ Search Error ({response.status_code}): {response.text}"
        except Exception as e:
            return f"❌ Search Exception: {e}"

    def _format_results(self, data: dict) -> str:
        """Format Tavily JSON response into a readable string for the agent."""
        output = []
        if data.get("answer"):
            output.append(f"💡 **AI Answer:** {data['answer']}\n")
        
        results = data.get("results", [])
        if not results:
            return "🔍 No relevant results found."

        output.append(f"🔍 Found {len(results)} sources:\n")
        for i, res in enumerate(results, 1):
            title = res.get("title", "Untitled")
            url = res.get("url", "#")
            content = res.get("content", "")[:300].replace("\n", " ")
            output.append(f"[{i}] **{title}**\n    🔗 {url}\n    📝 {content}...")
        
        return "\n".join(output)

    def _simulated_search(self, query: str) -> str:
        """Fallback to local artifact search when TAVILY_API_KEY is missing."""
        results = []
        base_dir = "swarm_v2_artifacts"
        
        # Scan local artifacts for relevant content
        query_words = query.lower().split()
        count = 0
        if os.path.exists(base_dir):
            for root, _, files in os.walk(base_dir):
                for file in files:
                    if count >= 3: break
                    if any(word in file.lower() for word in query_words) or file.endswith(".md"):
                        try:
                            path = os.path.join(root, file)
                            with open(path, "r", encoding="utf-8") as f:
                                content = f.read(200).replace("\n", " ")
                            results.append(f"[{len(results)+1}] **Local Knowledge: {file}**\n    🔗 {path}\n    📝 {content}...")
                            count += 1
                        except:
                            pass
        
        if not results:
            return (
                f"🔍 [SIMULATED] No local matches for: '{query}'\n"
                f"⚠️ TAVILY_API_KEY is not set. Suggesting DocIngestionSkill for deep learning."
            )

        header = f"🔍 [LOCAL KNOWLEDGE MOCK] Results for: '{query}' (No API Key)\n"
        return header + "\n\n".join(results)
