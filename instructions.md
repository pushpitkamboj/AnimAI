# AnimAI - Incremental Build Instructions

> 9 sequential prompts. Each builds on the output of all previous prompts.
> Feed these to an AI one at a time. Do not skip steps.
> Refer to `architecture.md` in this repo for full technical context.

---

## Prompt 1: Project Scaffold + State Schema + Dependencies

```
Create the project foundation for AnimAI — a system that converts natural language prompts into Manim animation videos.

Set up this directory structure:
  src/
    agent/
    rag/
    api/
    manim-worker/
    manim_docs/       (empty dir, will hold pre-extracted Manim docs later)

Create these files:

1. pyproject.toml — Python package "agent", requires-python >=3.10, dependencies:
   langgraph>=1.0.0, python-dotenv>=1.0.1, langchain>=1.0.0, chromadb>=1.2.0,
   fastapi>=0.119.0, pydantic>=2.12.3, langchain-openai>=0.1.0, requests>=2.32.0
   Dev deps: mypy, ruff, anyio, pytest, langgraph-cli[inmem]
   Build system: setuptools. Package dirs: "agent" = "src/agent"

2. requirements.txt — flat list: fastapi, uvicorn, langgraph, pydantic, chromadb,
   langchain, langchain-openai, requests, slowapi, langchain[google-genai]

3. .env.example — template with these keys (placeholder values):
   OPENAI_API_KEY, CHROMA_API_KEY, CHROMA_TENANT, CHROMA_DATABASE,
   R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET=manim-videos,
   MANIM_WORKER_URL, LANGSMITH_API_KEY, LANGSMITH_PROJECT, LANGSMITH_TRACING=true

4. src/agent/graph_state.py — The central state schema that ALL agent nodes will read/write:

   from typing_extensions import TypedDict
   from typing import Annotated
   from langgraph.graph.message import add_messages
   import operator

   class State(TypedDict):
       messages: Annotated[list, add_messages]
       prompt: str
       code: str
       instructions: Annotated[list, operator.add]
       mapped_chunks: Annotated[list, operator.add]
       sandbox_error: str
       video_url: str
       scene_name: str
       animation: bool
       non_animation_reply: str
       language: str

   The `instructions` and `mapped_chunks` fields use operator.add as the reducer
   so parallel node outputs get merged (this is critical for the fan-out RAG step later).
   The `messages` field uses add_messages reducer from LangGraph.

   Load dotenv at the top of this file.
```

---

## Prompt 2: RAG Subsystem — Chunking + Indexing

```
The project scaffold and State schema from Prompt 1 are in place.

Now build the RAG subsystem that indexes Manim library documentation into ChromaDB.
The agent will later query this to get relevant Manim API context when generating code.

Create two files:

1. src/rag/chunks.py — AST-based hierarchical chunking of Python source files.

   Function: create_hierarchy_chunks(source_code: str, file_path: str) -> List[List[Dict]]
   - Parse the source code with ast.parse()
   - For each ast.ClassDef node:
     PARENT CHUNK:
       - id = class_name
       - content = class definition from class line through __init__ method (if exists),
         otherwise just the class header. Use line numbers to extract source segments.
       - metadata: type="Class", file_path, children_ids (list of "ClassName.method_name"
         for all methods except __init__)
     CHILD CHUNKS (one per non-__init__ method):
       - id = "ClassName.method_name"
       - content = full method source
       - metadata: type="Method", file_path, method_name, parent_id=class_name
   - Return [parent_chunks_list, child_chunks_list]

   Helper: get_source_segment(source_code, start_line, end_line) extracts lines
   between start (inclusive) and end (exclusive) using splitlines.

   Wrapper: chunking(file_path: str, file_url: str) reads the file and calls
   create_hierarchy_chunks.

2. src/rag/indexing.py — Script to populate ChromaDB with the chunks.

   - Import chunking from chunks.py
   - Define files_to_index: a list of ~30 tuples (local_path, manim_docs_url) covering:
     Camera, Animation, mobject_frame, mobject_geometry_arc, mobject_geometry_boolean_ops,
     mobject_geometry_labelled, mobject_geometry_line, mobject_geometry_polygram,
     mobject_geometry_shape_matchers, mobject_geometry_tips, mobject_graph,
     mobject_graphing_coordinate_systems, mobject_graphing_functions,
     mobject_graphing_number_line, mobject_graphing_probability, mobject_graphing_scale,
     mobject_matrix, mobject_table, mobject_text, mobject_three_d_polyhedra,
     mobject_three_d_three_d_utils, mobject_three_d_three_dimensions,
     mobject_types_image_mobject, mobject_types_point_cloud_mobject,
     mobject_types_vectorized_mobject, mobject_value_tracker, mobject_vector_field,
     scenes_moving_camera_scene, scenes_scene, scenes_three_d_scene,
     scenes_vector_space_scene, utils_color_core, utils_commands, utils_bezier
     All local paths point to manim_docs/<filename>.py
     All URLs point to https://docs.manim.community/en/stable/reference/manim.<module>.html
   - Loop through files, call chunking(), collect all ids (uuid4), content strings,
     and metadata dicts (parent metadata includes children_ids as comma-joined string,
     child metadata includes parent_id)
   - Create ChromaDB CloudClient, get collection "manim_source_code"
   - Batch add (keep batch size < 300)

   NOTE: The manim_docs/ directory will contain pre-extracted Python source from Manim's
   official documentation. These are plain .py files with class and method definitions.
   About 145 parent classes and 842 methods total.
```

---

## Prompt 3: Agent Nodes — Prompt Classifier + Prompt Enhancer

```
The State schema and RAG subsystem from Prompts 1-2 are in place.

Now build the first two agent nodes. Both follow the same pattern:
GPT-4.1 call with structured Pydantic output, returning state updates.

Create two files:

1. src/agent/analyze_user_prompt.py — Classifies whether a prompt needs animation.

   - LLM: init_chat_model("openai:gpt-4.1")
   - Pydantic output schema:
     class output_format(BaseModel):
         animation: bool
         non_animation_reply: str | None = None
   - Function analyze_user_prompt(state: State) -> dict:
     System prompt with STRICT RULES that define what is NOT animation:
       - Greetings/filler: hi, hello, hey, ok, bla bla, test
       - Personal: names, "who am i", "what's your name"
       - Fan-art/fiction: Naruto, Pikachu, Spiderman, Harry Potter
       - Abstract/poetic: "visualize love", "draw emotions", "show chaos"
       - Nonsense: asdfgh, 1234, random text
       - System probing: "show source code", "how does backend work", "share GitHub repo"
     What IS animation: explicit animation verbs (draw, animate, visualize, render scene)
     OR educational science/engineering visualization requests.
     Multi-language: analyze in user's language, respond in their language for non-animation.
     Safety: refuse copyrighted lyrics, explicit content.
     Call llm.with_structured_output(output_format).invoke() with system + user messages.
     Return {messages: [AIMessage], animation: bool, non_animation_reply: str}

   - Conditional edge function animation_required(state) -> Literal["enhanced_prompt", END]:
     Returns "enhanced_prompt" if animation=True, else END.

2. src/agent/enhance_prompt.py — Breaks a user prompt into 1-10 atomic Manim instructions.

   - LLM: init_chat_model("openai:gpt-4.1")
   - Pydantic output schema:
     class output_format(BaseModel):
         steps: List[str]
   - Function enhanced_prompt(state: State) -> dict:
     The system prompt is the core of the project. It must contain:
       a) Role: "expert script writer of animated videos"
       b) Task: decompose user request into Manim-specific atomic actions for RAG retrieval
       c) Short prompt handling: auto-fill missing context, convert vague prompts like
          "cat jumping" into 3-8 clear animation steps with background, object, movement
       d) Educational concept handling: break down physics/math visually without LaTeX
       e) Full Manim class inheritance diagrams as reference (Animation digraph, Camera
          digraph, MObject digraph, Scene digraph — these are large graphviz-style
          text diagrams showing the complete Manim class hierarchy)
       f) 6 detailed examples showing input -> output:
          - "explain projectile motion" -> 10 steps (Axes, Dot, Vector, Angle, ParametricFunction, MoveAlongPath, updaters, Arrow, Succession)
          - "explain pythagoras theorem" -> 11 steps (Polygon/Triangle, Text labels, Line, Square mobjects with colors, FadeOut, Transform, Flash, final equation)
          - "show derivative of x^2" -> 12 steps (Axes, FunctionGraph, Dot P and Q, DashedLine, secant line, MoveAlongPath limit, Transform to tangent, derivative graph)
          - "explain area of circle" -> 10 steps (Circle with Sector decomposition, LaggedStart rearrangement, Transform to Rectangle, labels, GrowFromCenter)
          - "explain SHM" -> 11 steps (wall, Spring, Square block, DashedLine equilibrium, Vector force, Hooke's Law, oscillation, real-time FunctionGraph, period formula)
          - "explain normal distribution" -> 11 steps (Axes, FunctionGraph bell curve, DashedLine mean, sigma markers, shaded areas 68/95/99.7%, PDF formula, Transform for mean shift, shape change for sigma)
       g) Rules: limit to 1-10 instructions, each independent without losing context,
          no LaTeX, short/useful/technically sound
     Invoke with system + user prompt. Return {messages: [AIMessage], instructions: response.steps}
```

---

## Prompt 4: Agent Node — RAG Retrieval with Fan-Out

```
Prompt classifier and enhancer from Prompt 3 are in place. The State has an
`instructions` list (1-10 strings) populated by the enhancer.

Now build the RAG retrieval node that queries ChromaDB in parallel for each instruction.

Create src/agent/map_reduce.py:

   - ChromaDB setup: CloudClient using env vars CHROMA_API_KEY, CHROMA_DATABASE, CHROMA_TENANT

   - Function continue_instructions(state: State) -> list:
     This is a CONDITIONAL EDGE function (not a node). It uses LangGraph's Send() pattern
     to fan out one job per instruction:
       return [Send("get_chunks", {"instruction": instr}) for instr in state["instructions"]]
     This dispatches N parallel invocations of the get_chunks node.

   - Function get_chunks(state: State) -> dict:
     This is the NODE that runs once per instruction.
     - Read state["instruction"] (singular — set by Send, not from the main state)
     - Query ChromaDB collection "manim_source_code": collection.query(query_texts=[instruction], n_results=1)
     - Extract ids, documents, metadatas from the result
     - Build chunks list: [{id, text, metadata}] for each result
     - Return {"mapped_chunks": [{"instruction": instruction, "chunks": chunks}]}

     Because State.mapped_chunks uses Annotated[list, operator.add], the outputs from
     all parallel get_chunks invocations will be merged into a single list.

   The get_chunks node should be registered with a RetryPolicy in the graph later:
   max_attempts=3, initial_interval=1.0, backoff_factor=2.0
```

---

## Prompt 5: Agent Node — Code Generation

```
RAG retrieval from Prompt 4 is in place. The State now has `mapped_chunks`:
a list of {instruction: str, chunks: [{id, text, metadata}]} for each instruction.

Now build the code generation node — the most critical LLM call.

Create src/agent/generate_code.py:

   - LLM: init_chat_model("openai:gpt-4.1")
   - Pydantic output schema:
     class output_code(BaseModel):
         code: str
         scene_name: str

   - Function generate_code(state: State) -> dict:
     Build a system prompt that includes:
       a) Role: "expert Manim (Community Edition) developer for educational content"
       b) Input context: inject state["mapped_chunks"] directly into the prompt
       c) Code generation rules (all of these matter):
          - All imports explicit at top (no wildcard assumptions)
          - Must use VoiceoverScene base class with GTTSService
          - GTTS language = state["language"]
          - Safe area margins: 0.5 units, minimum spacing: 0.3 units
          - Modular helper functions for animation sequences
          - Comments for complex spatial logic
          - No external assets — procedural generation only
          - No `if __name__ == "__main__"` block
          - No BLACK text color — use BLUE_C, GREEN_C, GREY_A, GOLD_C, TEAL_C, WHITE
          - Animation timing synced to voiceover: run_time=tracker.duration
          - LaTeX packages via TexTemplate if needed
          - Manim plugins allowed if they simplify code
          - Performance best practices
       d) VoiceoverScene code example showing the expected pattern:
          class GTTSExample(VoiceoverScene):
              def construct(self):
                  self.set_speech_service(GTTSService(lang=<language>, tld="com"))
                  circle = Circle()
                  with self.voiceover(text="...") as tracker:
                      self.play(Create(circle), run_time=tracker.duration)
                  self.wait()
       e) Stage-based construct method structure (Stage 1, Stage 2, etc.)

     Invoke with system prompt + state["messages"]. Return {code: str, scene_name: str}
```

---

## Prompt 6: Manim Worker Service

```
This is an independent service — it doesn't import anything from the agent pipeline.

Create src/manim-worker/app.py — A standalone FastAPI rendering service.

   Endpoints:

   1. GET /health -> {"status": "ok"}

   2. POST /render:
      Input: JSON body with {code: str, scene_name: str, request_id?: str}
      Validation: both code and scene_name required, else HTTP 400

      Process:
      a) Generate request_id if not provided (uuid4)
      b) Get today's date as ISO string
      c) Write code to /tmp/{request_id}.py
      d) Run subprocess: manim -ql <file> <scene_name> --media_dir /tmp/media
         On CalledProcessError -> HTTP 500 "Manim failed: {error}"
      e) Verify video exists at /tmp/media/videos/{request_id}/480p15/{scene_name}.mp4
         If not -> HTTP 500 "Video not generated"
      f) Check SKIP_UPLOAD env var — if "1", return file:// URL (for local testing)
      g) Upload to Cloudflare R2:
         - boto3 S3 client with endpoint_url=https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com
         - Key: manim/{today}/{scene_name}/{request_id}.mp4
         - ContentType: video/mp4
         - On upload failure -> HTTP 500
      h) Return {video_url: public_r2_url, scene_name, request_id}
         Public URL pattern: https://pub-{R2_ACCOUNT_ID}.r2.dev/{key}

   Env vars needed: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET
```

---

## Prompt 7: Code Execution + Error Correction + Graph Wiring

```
All individual nodes (Prompts 3-5) and the Manim Worker (Prompt 6) are built.
Now connect everything.

Create three files:

1. src/agent/execute_code.py — Calls the Manim Worker via HTTP.
   - Function execute_code(state: State) -> dict:
     POST to {MANIM_WORKER_URL}/render with:
       {code: state["code"], scene_name: state["scene_name"], request_id: uuid4()}
     Timeout: 900 seconds
     On success: return {sandbox_error: "No error", video_url: data["video_url"]}
     NOTE: sandbox_error field name is kept for state schema compatibility.

2. src/agent/regenerate_code.py — Error detection + LLM code correction.
   - LLM: init_chat_model("openai:gpt-4.1")
   - Pydantic schema: output_code(BaseModel) with code: str, scene_name: str
   - Function is_valid_code(state: State) -> Literal["correct_code", END]:
     If state["sandbox_error"] == "No error" -> return END
     Else -> return "correct_code"
   - Function correct_code(state: State) -> dict:
     Prompt: "the code generated earlier has errors, see error - {sandbox_error}
     and the code is - {code}, this is manim code, fix the error using manim docs."
     Invoke with system prompt + state messages. Return {code, scene_name}

3. src/agent/graph.py — THE MAIN GRAPH. Wire everything together:

   from langgraph.graph import StateGraph, START, END
   from langgraph.checkpoint.memory import InMemorySaver
   from langgraph.types import RetryPolicy

   Import all node functions:
     analyze_user_prompt, animation_required (from analyze_user_prompt)
     enhanced_prompt (from enhance_prompt)
     get_chunks, continue_instructions (from map_reduce)
     generate_code (from generate_code)
     execute_code (from execute_code)
     is_valid_code, correct_code (from regenerate_code)

   Build the graph:
     graph = StateGraph(State)

     Add nodes:
       analyze_user_prompt
       enhanced_prompt
       get_chunks (with RetryPolicy: max_attempts=3, initial_interval=1.0, backoff_factor=2.0)
       generate_code
       correct_code
       execute_code

     Add edges:
       START -> analyze_user_prompt
       analyze_user_prompt -> conditional(animation_required) -> enhanced_prompt or END
       enhanced_prompt -> conditional(continue_instructions) -> [get_chunks]
       get_chunks -> generate_code
       generate_code -> execute_code
       execute_code -> conditional(is_valid_code) -> END or correct_code
       correct_code -> execute_code  (creates the retry loop)

     workflow_app = graph.compile()
```

---

## Prompt 8: FastAPI Layer + Semantic Caching + Rate Limiting

```
The LangGraph workflow (workflow_app) from Prompt 7 is compiled and ready.
Now wrap it in a production FastAPI application.

Create src/api/main.py:

   Setup:
   - Add src/ to sys.path for module resolution
   - Configure Python logging (INFO level, timestamped format)
   - Rate limiter: slowapi Limiter with get_remote_address as key function
   - FastAPI app with limiter attached to app.state
   - Add RateLimitExceeded exception handler
   - CORS middleware: allow_origins=["*"], allow_credentials=True, methods=["POST", "GET"]

   ChromaDB client:
   - CloudClient with CHROMA_API_KEY, CHROMA_DATABASE, CHROMA_TENANT from env
   - Cache threshold: THRESHOLD = 1 - 0.2 = 0.8 (distance-based, lower = more similar)

   Request model:
   - InstructionInput(BaseModel): prompt: str, language: str = "en"

   POST /run (rate limited: 10/minute):
   a) SEMANTIC CACHE CHECK:
      - Query collection "manim_cached_video_url" with the user's prompt, n_results=1
      - If distance <= THRESHOLD (0.8), return cached video_url immediately
        Response: {result: cached_url, status: "success"}
   b) RUN THE PIPELINE:
      - Generate thread_id (uuid4)
      - await workflow_app.ainvoke(
          input={"prompt": data.prompt, "language": data.language},
          config={"configurable": {"thread_id": thread_id}, "recursion_limit": 18}
        )
   c) HANDLE RESULTS:
      - If animation=False -> return {result: non_animation_reply, status: "non_animation"}
      - If success -> cache the result in ChromaDB (add prompt + video_url metadata),
        then return {result: video_url, status: "success"}
   d) ERROR HANDLING:
      - GraphRecursionError -> HTTP 422, {result: "Too difficult, give me something easier", status: "error"}
      - Generic Exception -> HTTP 500, {result: "Unexpected server error", status: "error"}

   GET /health:
   - Return {"message": "ok"}
```

---

## Prompt 9: Deployment Infrastructure + Frontend + Dev Tooling

```
The backend is fully functional from Prompts 1-8. Now add deployment and frontend.

Create these files:

1. Dockerfile (root) — for the animai-api service:
   FROM python:3.11-slim
   WORKDIR /app
   ENV PYTHONPATH=/app/src
   COPY requirements.txt, pip install, COPY all, EXPOSE 8000
   CMD: uvicorn src.api.main:app --host 0.0.0.0 --port 8000

2. langgraph.json — LangGraph platform deployment config:
   {
     "dependencies": ["."],
     "graphs": {
       "agent": "./src/agent/graph.py:workflow_app"
     },
     "env": ".env",
     "image_distro": "wolfi"
   }

3. Makefile — developer commands organized in sections:
   Config vars: PROJECT_ID=anim-482714, REGION=us-central1, SERVICE_NAME=animai-api,
     IMAGE_NAME=animai, REPO_NAME=animai-repo, IMAGE_URL constructed from these
   Sections:
     LOCAL DEV: install (pip install -r requirements.txt),
       dev (PYTHONPATH=src uvicorn src.api.main:app --reload --port 8000)
     TESTING: test (pytest unit), integration_tests (pytest integration),
       test-local (curl localhost health), test-local-run (curl POST /run),
       test-run (curl deployed /run), benchmark (hey load test)
     LINTING: lint (ruff check + format + mypy), format (ruff format + isort fix)
     DOCKER: docker-build (build + tag), docker-run (--env-file .env -p 8000:8000),
       docker-stop, docker-logs, docker-shell, docker-clean
     TERRAFORM: tf-init, tf-plan, tf-apply (-lock=false), tf-destroy
     GCP: gcp-auth, push (docker push), update (gcloud run services update)
     DEPLOY: deploy (docker-build + push + update), deploy-full (+ tf-apply)
     MONITORING: logs, logs-follow, describe, url
     CLEANUP: clean (__pycache__, .pyc, .pytest_cache, .mypy_cache)
     HELP: print all available commands

4. terraform/ directory with:
   - main.tf: Two Cloud Run services:
     animai-api: port 8000, 2 CPU/4GB, 0-10 instances, concurrency 10, timeout 300s
       env vars: OPENAI_API_KEY, LANGSMITH_*, CHROMA_*, MANIM_WORKER_URL (from manim-worker URI)
       health probes on /health
     manim-worker: port 8080, 2 CPU/4GB, 0-3 instances, concurrency 1, timeout 900s
       env vars: R2_*
       health probes on /health
     Artifact Registry repo, public IAM access for both services
   - variables.tf: all input variables
   - outputs.tf: service_url output
   - terraform.tfvars.example: template values

5. src/fe/ — Next.js 15 chat frontend (reference implementation):
   - package.json: next 15, react 19, typescript, tailwind 4, radix-ui components,
     react-player, react-hook-form, zod, @langchain/langgraph-sdk
   - app/page.tsx: Single-page chat interface
     State: messages array with {id, text, timestamp, videoUrl?, isResponse?, isLoading?, isError?}
     Message persistence: localStorage under key "animai_chat_history"
     Flow: user types -> add user msg -> add loading msg -> POST /api/generate ->
       on success: update loading msg with text + videoUrl
       on error: update loading msg with error state
     Layout: dark theme (bg-slate-950), TopBar + ChatInterface components
   - Components: TopBar (branding), ChatInterface (message list + input),
     MessageItem (renders text/loading/error), VideoPlayer (react-player),
     VideoModal (modal wrapper for video playback)
```

---

## Build Order Summary

| # | Scope | Key Output | Can Test? |
|---|-------|------------|-----------|
| 1 | Scaffold + State | Directory tree, deps, State TypedDict | `pip install -e .` |
| 2 | RAG subsystem | chunks.py, indexing.py | Run indexing script against manim_docs |
| 3 | Classifier + Enhancer | 2 agent nodes | Unit test each with mock state |
| 4 | RAG retrieval | map_reduce.py with Send | Needs ChromaDB populated from step 2 |
| 5 | Code generation | generate_code.py | Test with hardcoded mapped_chunks |
| 6 | Manim Worker | Standalone FastAPI service | `uvicorn` + curl /render |
| 7 | Execution + Graph | Full LangGraph pipeline | `workflow_app.ainvoke(...)` end-to-end |
| 8 | API layer | Production FastAPI + caching | `make dev` + curl /run |
| 9 | Deploy + Frontend | Docker, Terraform, Next.js | `make deploy` or `npm run dev` |
