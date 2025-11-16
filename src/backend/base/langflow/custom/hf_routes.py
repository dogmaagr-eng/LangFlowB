"""FastAPI router exposing minimal endpoints to load local HF models and generate text.

This file is intentionally small: it creates a module-level HFModelManager instance
and exposes a couple of safe endpoints to test local and remote inference.

Integrate the router into the application (include_router) where appropriate.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .hf_manager import HFModelManager

router = APIRouter(prefix="/custom/hf", tags=["custom-hf"])

manager = HFModelManager()


class LoadRequest(BaseModel):
    model_id: str
    key: Optional[str] = None
    device: Optional[str] = None


class GenRequest(BaseModel):
    model_key: str
    prompt: str
    max_new_tokens: Optional[int] = 128


class RemoteGenRequest(BaseModel):
    model: str
    prompt: str
    api_key: str
    api_url: Optional[str] = None


@router.post("/load_local")
def load_local(req: LoadRequest):
    try:
        key = manager.load_local(req.model_id, key=req.key, device=req.device)
        return {"status": "ok", "model_key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
def generate(req: GenRequest):
    try:
        text = manager.generate(req.model_key, req.prompt, max_new_tokens=req.max_new_tokens)
        return {"status": "ok", "output": text}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remote_generate")
def remote_generate(req: RemoteGenRequest):
    try:
        text = manager.call_hf_inference_api(req.model, req.prompt, req.api_key, api_url=req.api_url)
        return {"status": "ok", "output": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
