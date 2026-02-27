"""
HuggingFace Inference Brain
Provides direct transformers-based inference for google/gemma-3-270m-it.
Used as the executive layer in CognitiveStack when HF mode is enabled.
Advantages over Ollama for small models:
  - Full control over generation params (temperature, repetition_penalty, etc.)
  - Direct access to logits — better stop-token control
  - Can enforce structured output patterns via prefix forcing
"""

import asyncio
import logging
import re
import torch
from threading import Lock
from typing import Optional, Dict

logger = logging.getLogger("HFBrain")

_model = None
_tokenizer = None
_device = None
_lock = Lock()
_model_id = "microsoft/phi-4" # Upgraded for high-concurrency reasoning


def _get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _load_model():
    global _model, _tokenizer, _device
    with _lock:
        if _model is not None:
            return
        from transformers import AutoTokenizer, AutoModelForCausalLM
        logger.info(f"[HFBrain] Loading {_model_id}...")
        _device = _get_device()
        _tokenizer = AutoTokenizer.from_pretrained(_model_id)
        _model = AutoModelForCausalLM.from_pretrained(
            _model_id,
            torch_dtype=torch.float16 if _device == "cuda" else torch.float32,
            device_map="auto" if _device == "cuda" else None,
            low_cpu_mem_usage=True,
        )
        if _device == "cpu":
            _model = _model.to("cpu")
        _model.eval()
        logger.info(f"[HFBrain] {_model_id} loaded on {_device}.")


def _generate_sync(system_prompt: str, user_message: str, max_new_tokens: int = 256) -> Dict:
    """Run generation synchronously (called from thread pool)."""
    _load_model()
    
    # Build a chat-formatted prompt using the tokenizer's apply_chat_template
    messages = [
        {"role": "user", "content": f"{system_prompt}\n\n{user_message}"}
    ]

    try:
        input_text = _tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    except Exception:
        # Fallback if template not supported
        input_text = f"<start_of_turn>user\n{system_prompt}\n\n{user_message}<end_of_turn>\n<start_of_turn>model\n"

    inputs = _tokenizer(input_text, return_tensors="pt").to(_device if _device != "cpu" else "cpu")
    input_len = inputs["input_ids"].shape[1]

    with torch.no_grad():
        outputs = _model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,           # Greedy for determinism and speed
            temperature=1.0,
            repetition_penalty=1.2,   # Prevent repetitive looping
            pad_token_id=_tokenizer.eos_token_id,
        )

    # Decode only the new tokens
    new_tokens = outputs[0][input_len:]
    generated = _tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    # Extract <think> tags if present
    thought = ""
    content = generated
    if "<think>" in generated:
        match = re.search(r'<think>(.*?)</think>', generated, re.DOTALL)
        if match:
            thought = match.group(1).strip()
            content = re.sub(r'<think>.*?</think>', '', generated, flags=re.DOTALL).strip()

    if not content and thought:
        content = "[Internal processing active]"

    return {"content": content, "thought": thought}


async def hf_chat(system_prompt: str, user_message: str, max_new_tokens: int = 256) -> Dict:
    """Async wrapper for HF inference. Returns {content, thought}."""
    try:
        result = await asyncio.to_thread(_generate_sync, system_prompt, user_message, max_new_tokens)
        return result
    except Exception as e:
        logger.error(f"[HFBrain] Generation error: {e}")
        return {"content": f"[HFBrain Error] {type(e).__name__}: {e}", "thought": ""}


def is_model_loaded() -> bool:
    return _model is not None


def get_model_info() -> Dict:
    return {
        "model_id": _model_id,
        "device": _device or "not_loaded",
        "loaded": _model is not None,
    }
