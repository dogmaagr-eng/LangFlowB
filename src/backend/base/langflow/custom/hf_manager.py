"""Simple Hugging Face model manager for local models and HTTP API calls.

This module provides a minimal HFModelManager class that can:
- load small local models (via `transformers`)
- generate text using loaded models
- call Hugging Face Inference/other HTTP APIs

Notes:
- This is a lightweight scaffold to integrate into Langflow backend.
- Install runtime dependencies in your Python environment when ready: `transformers`, `torch` (or use MPS builds for Apple Silicon), and `requests`.
"""
from __future__ import annotations

import logging
import threading
from typing import Dict, Optional

import requests

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
except Exception:  # pragma: no cover - transformers may not be installed yet
    torch = None
    AutoModelForCausalLM = None
    AutoTokenizer = None

logger = logging.getLogger(__name__)


class HFModelManager:
    """Manage loaded Hugging Face models (minimal).

    Designed for small local models (Gemma 2B, T5 variant, CodeLlama small, etc.)
    on a developer machine. For production, add pooling, caching, and safety.
    """

    def __init__(self) -> None:
        self._models: Dict[str, dict] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _preferred_device() -> str:
        if torch is None:
            return "cpu"
        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def load_local(self, model_id: str, key: Optional[str] = None, device: Optional[str] = None, **kwargs) -> str:
        """Load a local HF model (or from hub) and return a model_key.

        model_id: path or HF repo id
        key: optional key to store model under (defaults to model_id)
        device: device string ('cpu','mps','cuda'). Defaults to auto-detect.
        kwargs: passed to `from_pretrained` (like trust_remote_code)
        """
        if AutoModelForCausalLM is None:
            raise RuntimeError("transformers is not installed in this environment")

        device = device or self._preferred_device()
        store_key = key or model_id

        with self._lock:
            if store_key in self._models:
                logger.debug("Model %s already loaded", store_key)
                return store_key

            logger.info("Loading model '%s' on device=%s", model_id, device)
            tokenizer = AutoTokenizer.from_pretrained(model_id, **kwargs)
            model = AutoModelForCausalLM.from_pretrained(model_id, **kwargs)

            # Move model to device if possible
            try:
                if device != "cpu" and torch is not None:
                    model.to(device)
            except Exception:
                logger.exception("Could not move model to device %s", device)

            self._models[store_key] = {
                "model": model,
                "tokenizer": tokenizer,
                "device": device,
            }

        return store_key

    def generate(self, model_key: str, prompt: str, max_new_tokens: int = 128, **gen_kwargs) -> str:
        """Generate text using a previously loaded model.

        Returns generated string.
        """
        with self._lock:
            info = self._models.get(model_key)
            if not info:
                raise KeyError(f"Model key not found: {model_key}")

            model = info["model"]
            tokenizer = info["tokenizer"]
            device = info.get("device", "cpu")

        if tokenizer is None or model is None:
            raise RuntimeError("Model or tokenizer missing")

        inputs = tokenizer(prompt, return_tensors="pt")

        if torch is not None and device != "cpu":
            try:
                inputs = {k: v.to(device) for k, v in inputs.items()}
            except Exception:
                logger.exception("Failed moving inputs to device %s", device)

        try:
            outputs = model.generate(**inputs, max_new_tokens=max_new_tokens, **gen_kwargs)
            text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            return text
        except Exception:
            logger.exception("Generation failed for model %s", model_key)
            raise

    def call_hf_inference_api(self, model: str, prompt: str, api_key: str, api_url: Optional[str] = None) -> str:
        """Call a Hugging Face-style inference API using HTTP.

        - `model` is the model id on the remote service.
        - `api_key` is used for Authorization.
        - `api_url` can override the default HF inference endpoint.
        """
        url = api_url or f"https://api-inference.huggingface.co/models/{model}"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {"inputs": prompt}
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # HF inference API can return different shapes; try to coerce to text
        if isinstance(data, list) and data:
            # common text generation response
            first = data[0]
            if isinstance(first, dict) and "generated_text" in first:
                return first["generated_text"]
            if isinstance(first, str):
                return first

        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"]

        # fallback: stringify
        return str(data)


__all__ = ["HFModelManager"]
