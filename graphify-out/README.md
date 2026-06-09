# Graphify Output

Generated for `/graphify .` on 2026-06-08.

## Files

- `langgraph-workflow.mmd` - active LangGraph control flow from `src/agent/graph.py`.
- `runtime-architecture.mmd` - request/runtime architecture from client to API, LangGraph, worker, cache, tracing, and storage.
- `module-map.mmd` - high-level module dependency map for the active backend.

## Main Runtime Path

```text
POST /run
  -> src/api/main.py
  -> src/agent/graph.py
  -> src/agent/execute_code.py
  -> manim-worker/app.py
  -> rendered video URL
```

## Notes

- The active production workflow is `src/agent/graph.py`.
- Fine-tune graph files under `src/agent/fine_tune_agent/` and `src/agent/graph_fine_tune.py` are legacy/reference paths.
- This environment did not have Graphviz `dot`, Mermaid CLI, or the project Python dependencies installed, so these artifacts are Mermaid source files rather than rendered PNG/SVG images.
