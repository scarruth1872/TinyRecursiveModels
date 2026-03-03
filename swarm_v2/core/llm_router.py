import os
import aiohttp
import json
import logging
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger("LLMRouter")

_HTTP_SESSION: Optional[aiohttp.ClientSession] = None

def get_session() -> aiohttp.ClientSession:
    global _HTTP_SESSION
    if _HTTP_SESSION is None or _HTTP_SESSION.closed:
        _HTTP_SESSION = aiohttp.ClientSession()
    return _HTTP_SESSION

async def generate_with_gemini(system_prompt: str, prompt: str, model_name: str = "gemini-2.5-flash") -> str:
    """Generate response using Google Gemini API."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "[Error] GEMINI_API_KEY not set in environment."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    payload = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 4096,
        }
    }
    
    session = get_session()
    async with session.post(url, json=payload) as resp:
        if resp.status != 200:
            err_text = await resp.text()
            return f"[Error] Gemini API failed: {err_text}"
        data = await resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return "[Error] Failed to parse Gemini response."

async def generate_with_openrouter(system_prompt: str, prompt: str, model_name: str = "anthropic/claude-3.5-sonnet") -> str:
    """Generate response using OpenRouter API."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return "[Error] OPENROUTER_API_KEY not set in environment."
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:8001",
        "X-Title": "Swarm OS V2",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 4096
    }
    
    session = get_session()
    async with session.post(url, headers=headers, json=payload) as resp:
        if resp.status != 200:
            err_text = await resp.text()
            return f"[Error] OpenRouter API failed: {err_text}"
        data = await resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return "[Error] Failed to parse OpenRouter response."

async def generate_with_deepseek(system_prompt: str, prompt: str, model_name: str = "deepseek-coder") -> str:
    """Generate response using DeepSeek API (OpenAI compatible)."""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return "[Error] DEEPSEEK_API_KEY not set in environment."
    
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 4096
    }
    
    session = get_session()
    async with session.post(url, headers=headers, json=payload) as resp:
        if resp.status != 200:
            err_text = await resp.text()
            return f"[Error] DeepSeek API failed: {err_text}"
        data = await resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return "[Error] Failed to parse DeepSeek response."

async def route_llm_request(backend: str, system_prompt: str, prompt: str, agent_name: str) -> Tuple[str, Optional[str]]:
    """
    Route the generation request to the appropriate LLM Regional Manager based on the agent's backend.
    Returns (response_text, reasoning_trace)
    """
    trace = None
    logger.info(f"Routing request for {agent_name} -> {backend}")
    
    try:
        if backend == "gemini":
            response = await generate_with_gemini(system_prompt, prompt)
        elif backend == "openrouter":
            response = await generate_with_openrouter(system_prompt, prompt)
        elif backend == "deepseek":
            response = await generate_with_deepseek(system_prompt, prompt)
        else:
            # Fallback to local Ollama/TRM reasoning if 'local' or unknown
            from swarm_v2.core.llm_brain import llm_chat
            response = await llm_chat(system_prompt, prompt)
            
        logger.info(f"Received response from {backend} for {agent_name}")
        return response, trace
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        print(f"[LLM Router] Critical Error with backend '{backend}': {err}")
        return f"[Error] Backend {backend} failed internally.", None
