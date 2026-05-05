# AnimAI Architecture

## Purpose

AnimAI turns a prompt into a rendered Manim video and returns a public URL.

The active runtime is intentionally narrow:

`POST /run` -> `src/api/main.py` -> `src/agent/graph.py` -> `src/agent/execute_code.py` -> `manim-worker/app.py`

## Active Services

### API

File:
[src/api/main.py](/Users/pushpitkamboj/PersonalProjects/AnimAI/src/api/main.py:1)

Responsibilities:

- exposes `/run` and `/health`
- normalizes `language` / `lang`
- performs semantic cache lookup against Chroma
- starts Langfuse request tracing
- invokes the active LangGraph workflow
- returns a video URL, non-animation reply, or error payload

### LangGraph Workflow

File:
[src/agent/graph.py](/Users/pushpitkamboj/PersonalProjects/AnimAI/src/agent/graph.py:1)

Active node sequence:

1. `analyze_user_prompt`
2. `route_prompt_for_grounding`
3. `build_topic_brief`
4. `plan_video`
5. `get_chunks`
6. `generate_code_outline`
7. `generate_code`
8. `execute_code`
9. recovery via `correct_code` or `simplify_code` when render fails

This is the only production graph used by `/run`.

### Render Worker

File:
[manim-worker/app.py](/Users/pushpitkamboj/PersonalProjects/AnimAI/manim-worker/app.py:1)

Responsibilities:

- accepts `POST /jobs`
- exposes `GET /jobs/{job_id}` for polling
- validates payload size and scene identifiers
- writes scene code into a request-scoped temp directory
- executes `manim`
- uploads the final `.mp4` to R2 or serves locally when upload is skipped
- emits worker-side Langfuse observations when configured

## End-to-End Flow

```text
User prompt
  -> POST /run
  -> semantic cache lookup
  -> prompt classification
  -> topic grounding and video planning
  -> retrieval of Manim context
  -> outline-first code generation
  -> POST /jobs to manim-worker
  -> poll job status every 5 seconds
  -> upload rendered asset
  -> return public video URL
```

## Main Code Areas

```text
AnimAI/
├── src/
│   ├── agent/            active graph, planning, retrieval orchestration, generation, recovery
│   ├── api/              FastAPI application
│   ├── observability/    Langfuse helpers
│   ├── rag/              retriever, reranker, query builder, chunks
│   ├── manim_docs/       Manim source/reference material
│   └── fe/               reference frontend copy
├── manim-worker/         dedicated render service
├── terraform/            deployment configuration
├── compose.yml           local API + worker stack
├── Dockerfile            API image
└── README.md
```

## Caching And Retrieval

- Semantic video cache:
  [src/api/main.py](/Users/pushpitkamboj/PersonalProjects/AnimAI/src/api/main.py:1)
- Retrieval stack:
  [src/rag/retriever.py](/Users/pushpitkamboj/PersonalProjects/AnimAI/src/rag/retriever.py:1),
  [src/rag/reranker.py](/Users/pushpitkamboj/PersonalProjects/AnimAI/src/rag/reranker.py:1),
  [src/rag/query_builder.py](/Users/pushpitkamboj/PersonalProjects/AnimAI/src/rag/query_builder.py:1)

The cache is for completed video outputs. Retrieval is for Manim-aware grounding during generation.

## Observability

Langfuse tracing is shared across the API, active graph nodes, and worker jobs through:

[src/observability/langfuse.py](/Users/pushpitkamboj/PersonalProjects/AnimAI/src/observability/langfuse.py:1)

The design intent is:

- request-level trace at the API boundary
- node-level spans in the active graph
- worker-side spans for render and upload
- trace propagation from API to worker using job payload metadata

## Local And Cloud Runtime

### Local

- `docker compose up --build`
- API listens on `:8000`
- worker listens on `:8080`

### Cloud

Terraform provisions two services:

- API service
- `manim-worker` service

The API talks to the worker over HTTP using `MANIM_WORKER_URL`.

## Legacy Experimental Graphs

These files are intentionally retained but deprecated:

- [src/agent/graph_fine_tune.py](/Users/pushpitkamboj/PersonalProjects/AnimAI/src/agent/graph_fine_tune.py:1)
- [src/agent/generate_code_fine_tune.py](/Users/pushpitkamboj/PersonalProjects/AnimAI/src/agent/generate_code_fine_tune.py:1)
- [src/agent/regenerate_code_fine_tune.py](/Users/pushpitkamboj/PersonalProjects/AnimAI/src/agent/regenerate_code_fine_tune.py:1)
- [src/agent/fine_tune_agent](/Users/pushpitkamboj/PersonalProjects/AnimAI/src/agent/fine_tune_agent)

They are not used by the active `/run` flow. They remain as legacy research/reference material only.
