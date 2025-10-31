# AnimAI — manim-app

This repository contains the Manim-based animation generation application and a LangGraph/LangChain agent for producing Manim scenes from natural language instructions. The project includes a RAG (retrieval-augmented generation) pipeline, agent logic, and an optional FastAPI endpoint for self-hosting.

## Table of contents
- Project summary
- Architecture
- Technologies used
- Deployment options
  1) Deploy with Langsmith / LangGraph platform
  2) Self-host (uncomment `src/api/main.py` and run FastAPI)
- Setup (local development)
- Codebase overview
- Troubleshooting & tips

## Project summary

The app translates user prompts into Manim commands via an LLM-backed agent and RAG index, then renders animations with Manim. It is designed to be run as a local service (FastAPI) or deployed via LangGraph/Langsmith flows.

## Architecture

- Agent layer: a LangChain/LangGraph agent composes prompts, applies retrieval (RAG) and issues Manim-specific instructions. Look under `src/agent`.
- RAG / indexing: vectors and chunking live in `src/rag` which indexes Manim-specific docs and commands.
- API: optional FastAPI endpoint is present at `src/api/main.py` (currently commented out by default; see "Self-host" section).
- Rendering: Manim code and helper modules live under `src/manim_docs` and other supporting directories.
- Deployment glue: optional LangGraph/graph definitions and Langsmith integration live in `langgraph.json` and `project_langraph_platform` style files used in other subprojects.

High-level flow:
1. User sends a prompt to the agent.
2. Agent enhances prompt and runs retrieval against the vector DB (RAG).
3. Agent produces a Manim script or a workflow that renders a video.
4. (Optional) API returns a video URL or status once rendering completes.

## Technologies used

- Python 3.10+
- Manim (for rendering animations)
- LangChain / langchain_core (agent building blocks)
- LangGraph (graph-based agent/workflow orchestration)
- Langsmith (optional tracing / deployment)
- FastAPI (optional HTTP API)
- Chroma / vector DB or other vector store used via RAG utilities
- SQLModel / SQLite (example local DB used in `fastAPI` sample)

Files that indicate these dependencies: `pyproject.toml`, `src/agent/*`, `src/rag/*`, `src/api/main.py`.

## Deployment options

1) Deploy through Langsmith / LangGraph

- When you have a LangGraph workflow / Langsmith-enabled project you can deploy the agent/graph directly on the LangGraph platform or use Langsmith tracing for observability.
- Basic steps (high level):
  - Create a Langsmith project and obtain `LANGSMITH_API_KEY`.
  - Ensure your graph (LangGraph) definitions are present (e.g. `langgraph.json` or your graph module).
  - Configure environment variables for any LLM provider keys (OPENAI_API_KEY or other provider vars) and `LANGSMITH_API_KEY`.
  - Use the LangGraph / Langsmith CLI or CI workflow to publish/deploy the graph. For project examples see `langraph/project_langraph_platform/pyproject.toml` for required package versions.

Notes:
- Langsmith deploy workflows vary by organization and platform; consult the Langsmith docs for concrete CLI commands. Typical CI workflows set `LANGSMITH_API_KEY` as a secret and enable tracing by `LANGSMITH_TRACING=true`.

2) Self-host (FastAPI)

This repo includes an API entrypoint at `src/api/main.py` which is currently commented out and marked "MIGRATED TO LANGGRAPH API FOR DEPLOYEMENT". To self-host the FastAPI endpoint, do the following:

- Edit `manimation/manim-app/src/api/main.py` and uncomment the code (remove the leading `#` from the top-level lines). The file contains a minimal FastAPI app with a `/run` endpoint that invokes the LangGraph workflow and a `/health` endpoint.
- Ensure your Python environment has the required dependencies (see Setup below).
- Run the app with uvicorn from the `manim-app` package root, for example:

```bash
# from project root: manimation/manim-app/
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

- The `/run` endpoint expects a JSON body with `prompt` and returns a JSON response with `result` containing `video_url` or an error status.

Notes and hints:
- If your API depends on `workflow_app` from `agent.graph`, verify that `workflow_app` is importable from the path used in the file and that any LangGraph-specific runtime is configured.
- CORS: the commented code includes a permissive CORS middleware; tighten origins in production.

## Setup (local development)

1. Clone the repo and change to the `manim-app` directory:

```bash
git clone <repo-url>
cd manimation/manim-app
```

2. Create a virtual environment and activate it:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies

This repository uses `pyproject.toml`. You can install with pip (editable) or via poetry if you prefer.

With pip (recommended for simple dev):

```bash
pip install -e .
# or if you have a requirements file: pip install -r requirements.txt
```

With poetry:

```bash
poetry install
```

4. Environment variables

Create a `.env` file or export env vars needed by your LLM provider and Langsmith, for example:

```bash
export OPENAI_API_KEY=sk-...
export LANGSMITH_API_KEY=lsv2_...
export LANGSMITH_TRACING=true
```

5. Run tests (quick verification)

```bash
pytest -q
```

6. Run the (optional) API

Uncomment `src/api/main.py` (see above) and run uvicorn:

```bash
python -m uvicorn src.api.main:app --reload
```

## Codebase overview

- `src/agent/` — agent code, prompt enhancement and workflow glue. Example: `src/agent/enhance_prompt.py`.
- `src/rag/` — indexing and chunking utilities for the retrieval layer.
- `src/api/main.py` — optional FastAPI endpoint (commented by default, intended for self-hosting if you prefer to bypass LangGraph managed runtime).
- `src/manim_docs/` — helper modules and Manim-specific code used for rendering.
- `pyproject.toml` — project dependencies and packaging.
- `langgraph.json` — LangGraph workflow definition used for LangGraph deployments.
- `tests/` — unit and integration tests.

## Example: call the API

POST /run with body: `{ "prompt": "Animate a circle turning into a square" }`.

Expected response JSON (success):

```json
{ "result": "https://.../generated_video.mp4", "status": "success" }
```

## Troubleshooting & tips

- If rendering takes too long, check your machine's resources and consider offloading rendering to a dedicated worker.
- If LangSmith tracing is not working, verify `LANGSMITH_API_KEY` and `LANGSMITH_TRACING=true`.
- If `workflow_app` imports fail after uncommenting the API, ensure `PYTHONPATH` includes project root or run via the package import path (as shown with `python -m uvicorn src.api.main:app`).

## Next steps (suggested)

- Add a `requirements-dev.txt` with pinned versions used in CI to make local setup reproducible.
- Add a tiny `docker-compose` that can launch a worker + API + vector DB for local end-to-end testing.

---

If you'd like, I can:
- create this README file in the repo (I will),
- also add a short `quickstart.md` or a `docker-compose.yml` to make local runs easier.

If you want me to install or pin exact dependency versions, tell me which environment (pip/poetry) you prefer and I'll update `pyproject.toml` or add `requirements.txt` snippets.
