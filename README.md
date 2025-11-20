# FastAPI RAG Practice

Minimal FastAPI project scaffold meant for experimenting with retrieval-augmented generation ideas.

## Getting started (uv)

1. Create a local virtual environment managed by `uv`:
   ```bash
   uv venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
2. Install dependencies straight from the `uv.lock` file:
   ```bash
   uv sync                 # runtime-only deps
   uv sync --extra dev     # include dev tools (pytest, httpx)
   ```
3. Launch the API with auto-reload using the virtualenv or via `uv run`:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

The server will start on http://127.0.0.1:8000 by default. Visit `/docs` for the interactive Swagger UI or `/redoc` for the ReDoc schema.

## Running tests

```bash
pytest                       # if your .venv is active
# or run without activating:
uv run --extra dev pytest
```
