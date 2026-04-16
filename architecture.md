# AnimAI - Architecture Document

## What It Does

AnimAI converts natural language prompts into educational Manim animation videos. A user types a concept (e.g., "explain projectile motion"), and the system generates a narrated, rendered `.mp4` video using Manim Community Edition, then returns a public URL to the video.

---

## Tech Stack

### Backend
- **Python 3.11** (runtime)
- **LangGraph + LangChain** — Agent workflow orchestration
- **OpenAI GPT-4.1** — LLM for prompt enhancement, code generation, error correction, prompt classification
- **FastAPI + Uvicorn** — REST API server
- **Manim (Community Edition)** — Animation rendering engine
- **manim-voiceover[gtts]** — Text-to-speech narration synced to animations
- **ChromaDB Cloud** — Vector database for RAG retrieval + semantic video caching
- **Cloudflare R2** — S3-compatible object storage for rendered videos
- **boto3** — R2 upload SDK
- **slowapi** — Rate limiting middleware
- **Pydantic v2** — Structured LLM output validation

### Frontend (separate repo, reference copy in `src/fe/`)
- **Next.js 15** + **React 19** + **TypeScript 5**
- **Tailwind CSS 4** + **Radix UI** — Styling and accessible components
- **react-player** — Video playback
- **@langchain/langgraph-sdk** — Backend communication

### Infrastructure
- **Docker** (Python 3.11-slim base)
- **Google Cloud Run** — Serverless container hosting
- **Google Artifact Registry** — Container image registry
- **Terraform** — Infrastructure-as-code for GCP provisioning

---

## Project Structure

```
AnimAI/
├── src/
│   ├── agent/                          # LangGraph agent pipeline
│   │   ├── graph.py                    # Main workflow graph (entry point)
│   │   ├── graph_state.py              # State schema (TypedDict)
│   │   ├── analyze_user_prompt.py      # Animation vs non-animation classifier
│   │   ├── enhance_prompt.py           # Breaks user prompt into Manim-specific steps
│   │   ├── map_reduce.py              # Parallel RAG retrieval via Send pattern
│   │   ├── generate_code.py            # Manim code generation from context + chunks
│   │   ├── execute_code_e2b.py         # Code execution via remote sandbox (async)
│   │   ├── execute_code.py             # Code execution via Manim Worker HTTP call
│   │   ├── regenerate_code.py          # Error detection + LLM-based code correction
│   │   └── fine_tune_agent/            # Alternative multi-stage pipeline (experimental)
│   │       ├── compile_graph.py        # Graph definition
│   │       ├── graph_state.py          # Extended state with scene plans, teaching framework
│   │       ├── nodes/                  # Individual pipeline stage implementations
│   │       └── prompts/                # Detailed system prompt templates
│   ├── rag/
│   │   ├── chunks.py                   # AST-based hierarchical chunking (class + method)
│   │   └── indexing.py                 # ChromaDB population script
│   ├── api/
│   │   └── main.py                     # FastAPI endpoints (/run, /health) with caching layer
│   ├── manim-worker/
│   │   └── app.py                      # Standalone Manim rendering service (/render, /health)
│   ├── manim_docs/                     # Pre-extracted Manim library source docs (~30 files)
│   └── fe/                             # Next.js frontend (reference copy)
├── terraform/                          # GCP Cloud Run + Artifact Registry IaC
├── Dockerfile                          # Main API container
├── Makefile                            # Dev, test, build, deploy commands
├── pyproject.toml                      # Python package config + dependencies
├── requirements.txt                    # Pip dependencies
├── langgraph.json                      # LangGraph platform deployment config
└── e2b.toml                            # Remote sandbox template config
```

---

## Architecture & Data Flow

### High-Level Pipeline

```
User prompt (text + language)
       │
       ▼
  ┌─────────────────┐
  │  POST /run       │  FastAPI endpoint, rate-limited 10/min
  └────────┬────────┘
           │
           ▼
  ┌─────────────────────┐
  │ Semantic Cache Check │  Query ChromaDB "manim_cached_video_url"
  │  (distance <= 0.2)  │  If hit → return cached video URL immediately
  └────────┬────────────┘
           │ cache miss
           ▼
  ┌─────────────────────┐
  │ analyze_user_prompt  │  GPT-4.1: classify as animation=true/false
  │                      │  Non-animation → return text reply, END
  └────────┬────────────┘
           │ animation=true
           ▼
  ┌─────────────────────┐
  │  enhanced_prompt     │  GPT-4.1: decompose into 1-10 atomic Manim instructions
  └────────┬────────────┘
           │
           ▼
  ┌─────────────────────┐
  │  continue_instructions│  Fan-out: Send() one job per instruction
  └────────┬────────────┘
           │ parallel
           ▼
  ┌─────────────────────┐
  │  get_chunks (x N)    │  For each instruction: query ChromaDB "manim_source_code"
  │                      │  Retrieve top-1 matching class/method chunk
  └────────┬────────────┘
           │ merge
           ▼
  ┌─────────────────────┐
  │  generate_code       │  GPT-4.1: produce full Manim VoiceoverScene class
  │                      │  Structured output → {code, scene_name}
  └────────┬────────────┘
           │
           ▼
  ┌─────────────────────┐
  │  execute_code        │  Manim Worker: write code → run `manim -ql` → upload to R2
  └────────┬────────────┘
           │
           ▼
  ┌─────────────────────┐
  │  is_valid_code       │  Check sandbox_error
  │                      │  "No error" → cache result + return video URL → END
  │                      │  Error → correct_code (GPT-4.1 fixes) → re-execute
  └─────────────────────┘
           │ max recursion_limit=18
           ▼
       Video URL returned
```

### Graph Definition (LangGraph)

```
START → analyze_user_prompt
                │
        ┌───────┴───────┐
        │               │
  animation=false   animation=true
        │               │
       END        enhanced_prompt
                        │
                continue_instructions (conditional fan-out)
                        │
                   get_chunks (parallel, per instruction)
                        │
                   generate_code
                        │
                   execute_code
                        │
                   is_valid_code
                   ┌────┴────┐
                   │         │
              No error     Error
                   │         │
                  END    correct_code ──→ execute_code (loop)
```

---

## Core Components (Detailed)

### 1. State Schema (`graph_state.py`)

```python
class State(TypedDict):
    messages: Annotated[list, add_messages]    # Conversation history
    prompt: str                                 # Original user input
    code: str                                   # Generated Manim Python code
    instructions: Annotated[list, operator.add] # Enhanced step-by-step instructions (1-10)
    mapped_chunks: Annotated[list, operator.add]# RAG results [{instruction, chunks}]
    sandbox_error: str                          # "No error" or error message
    video_url: str                              # Public R2 URL to rendered video
    scene_name: str                             # Manim scene class name
    animation: bool                             # Is this an animation request?
    non_animation_reply: str                    # Text reply for non-animation prompts
    language: str                               # Language code for TTS (e.g., "en", "hi")
```

### 2. Prompt Classifier (`analyze_user_prompt.py`)

- **LLM**: GPT-4.1 with structured output
- **Output**: `{animation: bool, non_animation_reply: str | None}`
- **Rejects**: Greetings, personal questions, copyrighted characters, abstract/poetic requests, nonsense, system probing
- **Passes**: Any educational/technical/visual animation request
- **Multi-language**: Analyzes and responds in the user's language

### 3. Prompt Enhancement (`enhance_prompt.py`)

- **LLM**: GPT-4.1 with structured output
- **Input**: Raw user prompt
- **Output**: `{steps: List[str]}` — 1 to 10 independent Manim-specific instructions
- **System prompt contains**:
  - Full Manim class inheritance diagrams (Animation, Camera, MObject, Scene)
  - 6 detailed examples (projectile motion, Pythagorean theorem, derivative of x^2, area of circle, SHM, normal distribution)
  - Rules: no LaTeX, auto-fill missing context, keep instructions independent, use exact Manim class names

### 4. RAG Retrieval (`map_reduce.py` + `rag/`)

- **Fan-out**: `continue_instructions()` uses LangGraph `Send()` to dispatch one `get_chunks` job per instruction (parallel execution)
- **Vector DB**: ChromaDB Cloud, collection `manim_source_code`
- **Query**: Semantic similarity search, `n_results=1` per instruction
- **Retry**: 3 attempts with exponential backoff (1s, 2s, 4s)
- **Result**: `mapped_chunks` list of `{instruction: str, chunks: [{id, text, metadata}]}`

#### RAG Indexing Pipeline (`rag/chunks.py` + `rag/indexing.py`)

- **Source**: 30+ pre-extracted Manim library documentation files in `manim_docs/`
- **Chunking**: AST-based hierarchical
  - **Parent chunk**: Class definition + `__init__` method (provides context)
  - **Child chunk**: Individual method definitions (provides detail)
  - **Metadata**: type (Class/Method), file_path, parent_id, children_ids
- **Stats**: ~145 parent classes, ~842 methods indexed

### 5. Code Generation (`generate_code.py`)

- **LLM**: GPT-4.1 with structured output
- **Input**: `mapped_chunks` (RAG context) + conversation `messages` + `language`
- **Output**: `{code: str, scene_name: str}`
- **Code structure requirements**:
  - Must extend `VoiceoverScene` with `GTTSService(lang=<user_language>)`
  - All Manim imports explicit, no implicit imports
  - Safe area margins: 0.5 units, minimum spacing: 0.3 units
  - Modular helper functions, no `if __name__`
  - No external assets (images/audio/video), procedural only
  - No BLACK text color — use BLUE_C, GREEN_C, GREY_A, GOLD_C, TEAL_C, WHITE, etc.
  - Animation synced to voiceover via `run_time=tracker.duration`

#### Generated Code Template

```python
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService

class SceneName(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService(lang="en", tld="com"))

        circle = Circle()
        with self.voiceover(text="This circle is drawn as I speak.") as tracker:
            self.play(Create(circle), run_time=tracker.duration)
        self.wait()
```

### 6. Code Execution — Manim Worker (`manim-worker/app.py`)

A standalone FastAPI service that renders Manim code and uploads the result.

**Endpoint**: `POST /render`  
**Input**: `{code: str, scene_name: str, request_id?: str}`  
**Process**:
1. Write code to `/tmp/{request_id}.py`
2. Run `manim -ql <file> <scene_name> --media_dir /tmp/media` via subprocess
3. Verify output exists at `/tmp/media/videos/{request_id}/480p15/{scene_name}.mp4`
4. Upload to Cloudflare R2 via boto3: key = `manim/{date}/{scene_name}/{request_id}.mp4`
5. Return `{video_url: <public_r2_url>, scene_name, request_id}`

**Rendering config**: `-ql` = low quality (480p, 15fps) for fast turnaround

**R2 upload**:
```python
s3 = boto3.client("s3",
    endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
)
s3.upload_file(video_path, R2_BUCKET, key, ExtraArgs={"ContentType": "video/mp4"})
public_url = f"https://pub-{R2_ACCOUNT_ID}.r2.dev/{key}"
```

### 7. Error Correction Loop (`regenerate_code.py`)

- **Trigger**: `sandbox_error != "No error"`
- **LLM**: GPT-4.1 with structured output
- **Input**: Error message + original code + conversation messages
- **Output**: Corrected `{code, scene_name}`
- **Flow**: `correct_code → execute_code → is_valid_code` (loops until success or recursion limit of 18)

### 8. Semantic Video Caching (in `api/main.py`)

- **Collection**: `manim_cached_video_url` in ChromaDB
- **Threshold**: Distance <= 0.2 (80% similarity) = cache hit
- **On hit**: Return cached `video_url` immediately, skip entire pipeline
- **On miss**: Run full pipeline, then `collection.add(...)` to cache the result

---

## API Specification

### `POST /run`

```
Request:
{
  "prompt": "explain projectile motion",  // required
  "language": "en"                         // optional, default "en"
}

Response (success):
{
  "result": "https://pub-xxx.r2.dev/manim/2026-04-16/SceneName/uuid.mp4",
  "status": "success"
}

Response (non-animation):
{
  "result": "Hello! I can help you visualize educational concepts. Try asking me to animate something!",
  "status": "non_animation"
}

Response (too complex):
{
  "result": "That was too difficult to process for me, give me something easier :)",
  "status": "error"
}     // HTTP 422

Response (server error):
{
  "result": "An unexpected server error occurred. Please try again later.",
  "status": "error"
}     // HTTP 500
```

### `GET /health`

```
Response: { "message": "ok" }
```

**Rate limit**: 10 requests/minute per IP (slowapi)  
**CORS**: `allow_origins=["*"]`, methods `POST` and `GET`

---

## Frontend Architecture (`src/fe/`)

- **Single-page chat interface** with message history persisted in localStorage
- **Message types**: user text, loading spinner, response with optional video URL, error
- **Flow**: User types prompt → `POST /api/generate` (Next.js route) → backend `/run` → response displayed with embedded video player
- **Video playback**: `react-player` component in a modal
- **Production frontend**: Hosted separately (Vercel), this copy is for reference

---

## Environment Variables

```
# LLM
OPENAI_API_KEY=sk-...

# ChromaDB
CHROMA_API_KEY=...
CHROMA_TENANT=...
CHROMA_DATABASE=...

# Cloudflare R2 (video storage)
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=manim-videos

# Manim Worker
MANIM_WORKER_URL=https://manim-worker-xxxxx.run.app

# Observability
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=...
LANGSMITH_TRACING=true
```

---

## Deployment Architecture

### Two-Service Model (GCP Cloud Run via Terraform)

```
Internet
    │
    ▼
┌──────────────────┐         ┌──────────────────┐
│  animai-api       │ ──────▶│  manim-worker     │
│  (FastAPI)        │  HTTP   │  (FastAPI)        │
│  Port 8000        │         │  Port 8080        │
│  2 CPU / 4GB RAM  │         │  2 CPU / 4GB RAM  │
│  0-10 instances   │         │  0-3 instances    │
│  concurrency: 10  │         │  concurrency: 1   │
│  timeout: 300s    │         │  timeout: 900s    │
└──────────────────┘         └──────────────────┘
         │                            │
         ▼                            ▼
   ChromaDB Cloud              Cloudflare R2
   (RAG + Cache)              (Video Storage)
```

- **animai-api**: Runs the LangGraph agent pipeline, handles API requests
- **manim-worker**: Dedicated rendering service, concurrency=1 (one render at a time per instance), long timeout for heavy renders
- **Both publicly accessible** (IAM: allUsers → roles/run.invoker)

### Build & Deploy

```bash
make deploy          # docker-build → push to Artifact Registry → update Cloud Run
make deploy-full     # docker-build → push → terraform apply
```

### Docker (animai-api)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH=/app/src
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Manim Worker Container Requirements

The manim-worker container needs:
- Python 3.11+
- FFmpeg
- LaTeX (texlive-latex-recommended, cm-super, dvipng)
- Cairo + Pango (libcairo2-dev, libpango1.0-dev)
- Manim (`pip install manim`)
- manim-voiceover with GTTS (`pip install "manim-voiceover[gtts]"`)
- boto3 (for R2 upload)

---

## LangGraph Platform Deployment (Alternative)

The project can also deploy via LangGraph Cloud:

```json
// langgraph.json
{
  "graphs": {
    "agent": "./src/agent/graph.py:workflow_app",
    "agent_fine_tune": "./src/agent/graph_fine_tune.py:workflow_app_fine_tune",
    "agent_fine_tune2": "./src/agent/fine_tune_agent/compile_graph.py:workflow_app_fine_tune2"
  },
  "env": ".env",
  "image_distro": "wolfi"
}
```

This exposes the graph as a managed API with built-in checkpointing, streaming, and LangSmith tracing.

---

## Fine-Tune Agent (Experimental — `fine_tune_agent/`)

An alternative, more granular pipeline. Currently partially disabled (some nodes commented out).

**Pipeline**: `scene_plan → technical_implementation → generate_code → execute_code → [correct_code loop]`

**Extended State** includes:
- `IndividualScene` — title, description, purpose per scene
- `TechnicalImplementationPlan` — Manim objects, VGroups, positioning, animation sequence, safety checks
- `TeachingFrameworkPlan` — Learning objectives, engagement strategies (disabled)
- `AnimationNarrationPlan` — Pedagogical plan, narration scripts, sync strategy (disabled)

---

## Key Design Decisions

- **Structured LLM outputs everywhere**: All LLM calls use `with_structured_output(PydanticModel)` for type-safe, parseable responses
- **Parallel RAG retrieval**: LangGraph `Send()` pattern fans out one query per instruction, merged via `Annotated[list, operator.add]`
- **Hierarchical RAG chunks**: Parent (class + init) gives context, child (method) gives API detail — both stored in same collection with parent/child metadata links
- **Semantic caching**: Avoids re-rendering similar prompts by checking ChromaDB distance before running the pipeline
- **Separation of rendering**: Manim Worker runs as an isolated service with concurrency=1, preventing resource contention during CPU-intensive renders
- **Error self-correction**: LLM sees its own errors and regenerates code, up to recursion_limit=18
- **Multi-language TTS**: Language passed through the entire pipeline to GTTSService, voiceover narration generated in user's language
- **No external assets**: All visuals are procedurally generated Manim code — no images, audio files, or video clips required
