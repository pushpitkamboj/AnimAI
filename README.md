<p align="center">
  <a href="https://github.com/pushpitkamboj/AnimAI">
    <img src="https://raw.githubusercontent.com/pushpitkamboj/AnimAI/main/arch_image.png" alt="Architecture" width="900"/>
  </a>
</p>

<p align="center">
  <a href="https://github.com/pushpitkamboj/AnimAI"><img src="https://img.shields.io/badge/AnimAI-manimation-blue?logo=github" alt="AnimAI"/></a>
  <a href="https://github.com/pushpitkamboj/AnimAI/actions"><img src="https://img.shields.io/github/workflow/status/pushpitkamboj/AnimAI/CI?label=ci&logo=github" alt="build"/></a>
  <a href="https://pypi.org/"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="python"/></a>
  <a href="https://github.com/pushpitkamboj/AnimAI/blob/main/LICENSE"><img src="https://img.shields.io/github/license/pushpitkamboj/AnimAI" alt="license"/></a>
</p>

# AnimAI

AnimAI converts natural-language prompts into Manim videos.

The active backend is a small server-side pipeline:

`POST /run` -> `src/api/main.py` -> `src/agent/graph.py` -> `src/agent/execute_code.py` -> `manim-worker/app.py`

The API plans and generates Manim code, submits it to a dedicated render worker, polls every 5 seconds for job status, and returns a public video URL on success.

## Current Architecture

- `src/api/main.py`
  FastAPI entrypoint with language normalization, semantic cache lookup, Langfuse tracing, and the `/run` + `/health` endpoints.
- `src/agent/graph.py`
  Active LangGraph workflow for prompt classification, grounding, planning, retrieval, generation, execution, and recovery.
- `src/agent/execute_code.py`
  Submit-and-poll client for the render worker.
- `manim-worker/app.py`
  Dedicated Manim execution service with `/jobs` and `/jobs/{job_id}`.
- `src/rag/`
  Retrieval stack and supporting chunks for Manim-aware grounding.
- `src/manim_docs/`
  Manim reference material used for retrieval/indexing.

## Legacy Code

The repository still keeps the fine-tune graph experiments under:

- `src/agent/graph_fine_tune.py`
- `src/agent/generate_code_fine_tune.py`
- `src/agent/regenerate_code_fine_tune.py`
- `src/agent/fine_tune_agent/`

These files are legacy experimental pipelines. They are not part of the active production request flow and are kept only as reference material.

## Frontend Note

The code in `src/fe/` is not the source of truth for production frontend work.

Production frontend repo:
`https://github.com/AnshBansalOfficial/v0-anim-ai`

## Local Development

### Docker

```bash
docker compose up --build
```

This starts:

- API on `http://localhost:8000`
- Manim worker on `http://localhost:8080`

### Direct API run

```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

If you run the API directly, you should also run the worker separately:

```bash
uvicorn app:app --app-dir manim-worker --host 0.0.0.0 --port 8080 --reload
```

## Request Example

```bash
curl -X POST http://localhost:8000/run \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"2 squares rotating","language":"en"}'
```

Example response:

```json
{"result":"https://.../scene.mp4","status":"success"}
```

## Environment

Common environment variables:

- `OPENAI_API_KEY`
- `MANIM_WORKER_URL`
- `CHROMA_API_KEY`
- `CHROMA_DATABASE`
- `CHROMA_TENANT`
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET`
- `R2_PUBLIC_BASE_URL`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_BASE_URL` or `LANGFUSE_HOST`
- `LANGFUSE_TIMEOUT` optional, defaults to `15` in this app
- `LANGFUSE_FLUSH_AT` optional, defaults to `64` in this app
- `LANGFUSE_FLUSH_INTERVAL` optional, defaults to `2` in this app
- `LANGFUSE_TRACING_ENVIRONMENT` optional, e.g. `development`
- `LANGFUSE_AUTH_CHECK_ON_STARTUP` optional, set to `true` for a startup connectivity check

## Testing

```bash
pytest -q
```

## License

See [LICENSE](/Users/pushpitkamboj/PersonalProjects/AnimAI/LICENSE).
