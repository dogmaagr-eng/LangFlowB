Custom Hugging Face integration (scaffold)
========================================

What this folder provides
-------------------------

- `hf_manager.py`: a minimal HFModelManager to load small local Hugging Face models (or from the Hub) and to call HF-style HTTP inference APIs.
- `hf_routes.py`: a tiny FastAPI router exposing endpoints for quick local testing (`/custom/hf/load_local`, `/custom/hf/generate`, `/custom/hf/remote_generate`).

Quick setup (developer machine, macOS M1)
----------------------------------------

1) Create a virtualenv and install runtime deps (example):

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
# Install core dependencies for local HF testing
pip install "transformers>=4.30" "torch" requests
```

Notes about Apple Silicon (M1/M2):
- For best performance with native Apple silicon, install a torch build that supports MPS. See PyTorch installation instructions for macOS / MPS.
- Small models (2B) may still require significant RAM — prefer quantized runtimes (not included here) for light-weight local usage.

How to use
----------

1) Load a model (POST JSON to `/custom/hf/load_local`):

```json
{ "model_id": "path_or_hf_repo_id", "key": "optional_key" }
```

2) Generate with a loaded model (POST to `/custom/hf/generate`):

```json
{ "model_key": "the_key_returned", "prompt": "Write a simple React component" }
```

3) Or call a remote HF inference endpoint (POST to `/custom/hf/remote_generate`):

```json
{ "model": "gpt-...", "prompt": "Hello", "api_key": "hf_xxx" }
```

Integration notes
-----------------

- This scaffold intentionally does not auto-register the router with Langflow's main application to avoid surprising changes. To enable the endpoints, import and include `custom.hf_routes.router` in the FastAPI app startup (e.g. `app.include_router(...)`).
- For production use add auth, rate-limiting, model lifecycle management and persistence.

Next steps I can implement for you
---------------------------------

- Register the router in the Langflow backend and add pairing tests.
- Create DB schema for projects and persistent context (Postgres/SQLite migrations).
- Add orchestration scaffolding that runs multiple models in steps (isolated contexts) and assembles results.
- Build Framer component generation pipeline and a preview renderer in the frontend.

Tell me which of the next steps you want me to take now and I will proceed.
