<!-- Top-level decorative header and architecture image -->
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

# AnimAI — manim-app

An opinionated Manim-based animation generator that converts natural language prompts into Manim scenes using LangChain/LangGraph agents, a RAG index and optional HTTP API.

> Beautiful, reproducible animations—driven by LLMs + retrieval.

## Table of contents

- [Project summary](#project-summary)
- [Architecture](#architecture)
- [Technologies used](#technologies-used)
- [Deployment options](#deployment-options)
  - [1) Langsmith / LangGraph](#1-deploy-through-langsmith--langgraph)
  - [2) Self-host (FastAPI)](#2-self-host-fastapi)
- [Quickstart (local)](#quickstart-local)
- [Codebase overview](#codebase-overview)
- [Examples](#examples)
- [Troubleshooting & tips](#troubleshooting--tips)
- [Contributing](#contributing)
- [License](#license)

## Project summary

The app translates user prompts into Manim commands via an LLM-backed agent and RAG index, then renders animations with Manim. It is designed to be run as a local service (FastAPI) or deployed via LangGraph/Langsmith flows.

## Architecture

- Agent layer — LangChain / LangGraph agent composes, enhances and executes prompts. See `src/agent/`.
- Retrieval (RAG) — document chunking and vector indexing in `src/rag/` to make Manim commands and docs searchable.
- API — optional FastAPI endpoint at `src/api/main.py` (commented by default; see Self-host section).
- Renderer — Manim scenes and helpers live under `src/manim_docs/` and are used to produce final video assets.
- Storage / delivery — produced videos are uploaded (example: Cloudflare R2) and returned as URLs by the API.

High-level flow
1. User sends a natural language prompt to the agent.
2. Agent enhances the prompt and issues RAG queries to the vector store.
3. Agent produces a Manim script or workflow; rendering is performed by a worker running Manim.
4. Rendered video is stored and the API returns a shareable URL or status.

## Technologies used

- Python 3.10+
- Manim (rendering)
- LangChain / langchain_core (agent logic)
- LangGraph (workflow orchestration)
- Langsmith (optional tracing & deployment)
- FastAPI (optional REST endpoint)
- Chroma or other vector store (RAG)
- SQLModel / SQLite (examples)

Key files: `pyproject.toml`, `src/agent/`, `src/rag/`, `src/api/main.py`.

## Deployment options

### 1) Deploy through Langsmith / LangGraph

- Use LangGraph to publish the workflow/graph; Langsmith can be used for tracing and CI-based deployments.
- Steps (high level):
  1. Get `LANGSMITH_API_KEY` and set it in your CI or environment.
  2. Confirm `langgraph.json` or your graph module is up to date.
  3. Use platform-specific CLI/CI to publish the graph (CI should set `LANGSMITH_API_KEY` as secret and may set `LANGSMITH_TRACING=true`).

See `langraph/project_langraph_platform/pyproject.toml` for compatible package versions used in examples.

### 2) Self-host (FastAPI)

This project contains a commented FastAPI entrypoint at `src/api/main.py` (marked "MIGRATED TO LANGGRAPH API FOR DEPLOYEMENT"). To enable self-hosting:

1. Open `manimation/manim-app/src/api/main.py` and uncomment the FastAPI app code. The endpoints provided are `/run` (POST) and `/health` (GET).
2. Ensure dependencies are installed (see Quickstart below).
3. Run the app from the `manim-app` root:

```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

The `/run` endpoint expects `{ "prompt": "..." }` and will return a `result` (a `video_url` on success) and `status`.

Production notes: ensure `PYTHONPATH` includes the project root or use package-style imports. Replace permissive CORS with specific origins. Consider running the renderer as a background worker or container for heavier workloads.

## Quickstart (local)

1. Clone and change directory

```bash
git clone https://github.com/pushpitkamboj/AnimAI
cd manimation/manim-app
```

2. Create and activate a venv

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies

```bash
pip install -e .
# or: poetry install
```

4. Environment variables (example)

```bash
export OPENAI_API_KEY=sk-...
export LANGSMITH_API_KEY=lsv2_...
export LANGSMITH_TRACING=true
```

5. Run unit tests

```bash
pytest -q
```

6. Start the optional API (if uncommented)

```bash
python -m uvicorn src.api.main:app --reload
```

## Codebase overview

- `src/agent/` — agent code and prompt enhancement (`enhance_prompt.py`).
- `src/rag/` — chunking and indexing utilities for RAG.
- `src/api/main.py` — optional FastAPI endpoint (commented by default).
- `src/manim_docs/` — Manim helper modules and example scene code.
- `pyproject.toml` — dependencies and packaging metadata.
- `langgraph.json` — LangGraph workflow definition used for deployments.
- `tests/` — unit and integration tests.

## Examples

1) Call the API (if self-hosted)

POST /run

Request body:

```json
{ "prompt": "Animate a circle turning into a square" }
```

Response (success):

```json
{ "result": "https://.../generated_video.mp4", "status": "success" }
```

2) Run a quick local render (example developer flow)

```bash
# Create a prompt payload and POST to /run, or call the agent runner directly from a script
python -c "from src.agent.enhance_prompt import enhance; print(enhance('Make a bouncing ball'))"
```

## Troubleshooting & tips

- Rendering slow? Use a dedicated worker or scale compute for Manim tasks. Reduce resolution for testing.
- Langsmith tracing failing? Confirm `LANGSMITH_API_KEY` and `LANGSMITH_TRACING=true`.
- Import errors after enabling API? Ensure you run from repo root and `PYTHONPATH` includes project root or run with `python -m uvicorn src.api.main:app`.

## Contributing

Contributions are welcome! Typical workflow:

1. Fork the repo
2. Create a feature branch
3. Add tests and documentation
4. Open a pull request

Please follow pep8 formatting and add unit tests for new features.

## License

This project includes a `LICENSE` file in the repository root. Review it for licensing details.

---

If you'd like I can also:

- add a `docker-compose.yml` for local testing (worker + API + vector DB),
- create a `quickstart.md` with screenshots and sample prompts, or
- pin dependency versions and add `requirements-dev.txt`.
