import logging
import os
from uuid import uuid4

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langgraph.errors import GraphRecursionError
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from chroma_utils import chroma_query_enabled, get_chroma_cloud_client, get_chroma_embedding_function

try:
    import httpx
except Exception:  # pragma: no cover - httpx is installed transitively in runtime
    httpx = None

try:
    from openai import APITimeoutError
except Exception:  # pragma: no cover - local env may not have openai installed
    APITimeoutError = None

load_dotenv()

from agent.graph import workflow_app
from observability.langfuse import (
    auth_check_langfuse,
    configure_langfuse,
    get_langfuse_handler,
    propagate_langfuse_attributes,
)


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

# Keep semantic cache close to exact-match territory so new prompts still exercise the pipeline.
THRESHOLD = 0.05
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="AnimAI API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    prompt: str
    language: str = "en"


@app.on_event("startup")
async def startup_event() -> None:
    configure_langfuse()
    if os.getenv("LANGFUSE_AUTH_CHECK_ON_STARTUP", "").lower() == "true":
        auth_check_langfuse()


def _generation_error_status_code(error_message: str) -> int:
    normalized = error_message.lower()
    if "timed out" in normalized:
        return 504
    if "failed to submit render job" in normalized or "failed to poll render job" in normalized:
        return 502
    if "manim_worker_url is not configured" in normalized:
        return 503
    return 500


def _semantic_cache_enabled() -> bool:
    return os.getenv("SEMANTIC_CACHE_ENABLED", "").lower() == "true"


def _iter_exception_chain(exc: BaseException):
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        yield current
        seen.add(id(current))
        current = current.__cause__ or current.__context__


def _is_timeout_exception(exc: BaseException) -> bool:
    timeout_types: tuple[type[BaseException], ...] = tuple(
        timeout_type
        for timeout_type in (
            TimeoutError,
            requests.Timeout,
            APITimeoutError,
            getattr(httpx, "TimeoutException", None),
        )
        if timeout_type is not None
    )

    for err in _iter_exception_chain(exc):
        if timeout_types and isinstance(err, timeout_types):
            return True

        error_name = err.__class__.__name__.lower()
        error_message = str(err).lower()
        if "timeout" in error_name or "timed out" in error_message:
            return True

    return False


def _get_cache_collection():
    if not _semantic_cache_enabled():
        logger.info("Semantic cache disabled")
        return None

    if not chroma_query_enabled():
        logger.info(
            "Chroma cache disabled because Cloud credentials or embedding API key are missing"
        )
        return None

    client = get_chroma_cloud_client()
    embedding_function = get_chroma_embedding_function()
    if client is None or embedding_function is None:
        logger.info("Chroma cache disabled because the client or embedding function is unavailable")
        return None

    return client.get_or_create_collection(
        name="manim_cached_video_url",
        embedding_function=embedding_function,
    )


def _get_cached_video_url(prompt: str) -> str | None:
    try:
        collection = _get_cache_collection()
        if collection is None:
            return None

        result = collection.query(query_texts=[prompt], n_results=1)
        distances = result.get("distances", [[]])
        metadatas = result.get("metadatas", [[]])
        if not distances or not metadatas:
            return None

        distance = distances[0][0]
        metadata = metadatas[0][0] or {}
        if distance is not None and distance <= THRESHOLD:
            return metadata.get("video_url")
        return None
    except Exception:
        logger.warning("Skipping semantic cache lookup after Chroma failure", exc_info=True)
        return None


def _cache_video_url(prompt: str, video_url: str) -> None:
    try:
        collection = _get_cache_collection()
        if collection is None:
            return
        collection.add(
            ids=[str(uuid4())],
            documents=[prompt],
            metadatas=[{"video_url": video_url}],
        )
    except Exception:
        logger.warning("Skipping semantic cache write after Chroma failure", exc_info=True)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"message": "ok", "executor": "manim-worker"}


@app.post("/run")
@limiter.limit("10/minute")
async def run_pipeline(payload: RunRequest, request: Request):
    thread_id = str(uuid4())
    language = payload.language.strip() or "en"
    client_host = request.client.host if request.client else "unknown"
    trace_metadata = {
        "feature": "animation_run",
        "language": language,
        "endpoint": "/run",
        "client_host": client_host,
    }

    try:
        with propagate_langfuse_attributes(
            session_id=thread_id,
            tags=["animai", "api", "animation"],
            metadata=trace_metadata,
            trace_name="animation-api-request",
        ):
            cached_url = _get_cached_video_url(payload.prompt)
            if cached_url:
                logger.info("Semantic cache hit for prompt")
                return {"result": cached_url, "status": "success"}

            workflow_config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 20,
                "run_name": "animation-langgraph-workflow",
                "metadata": {
                    "langfuse_session_id": thread_id,
                    "langfuse_tags": ["animai", "langgraph", "animation"],
                    "feature": "animation_run",
                    "language": language,
                },
            }
            langfuse_handler = get_langfuse_handler()
            if langfuse_handler is not None:
                workflow_config["callbacks"] = [langfuse_handler]

            logger.info(
                "Running workflow for thread_id=%s with language=%s from client=%s",
                thread_id,
                language,
                client_host,
            )
            result = await workflow_app.ainvoke(
                input={"prompt": payload.prompt, "language": language},
                config=workflow_config,
            )

            if not result.get("animation", True):
                return {"result": result.get("non_animation_reply", ""), "status": "non_animation"}

            video_url = result.get("video_url")
            if not video_url:
                sandbox_error = (result.get("sandbox_error") or "").strip()
                status_code = _generation_error_status_code(sandbox_error)
                return JSONResponse(
                    status_code=status_code,
                    content={
                        "result": sandbox_error or "Video generation failed after multiple attempts",
                        "status": "error",
                    },
                )

            _cache_video_url(payload.prompt, video_url)
            return {"result": video_url, "status": "success"}
    except GraphRecursionError:
        return JSONResponse(
            status_code=500,
            content={
                "result": "Video generation failed after maximum recovery attempts",
                "status": "error",
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        if _is_timeout_exception(exc):
            logger.warning("Upstream timeout while processing animation request", exc_info=True)
            return JSONResponse(
                status_code=504,
                content={
                    "result": "Upstream service timed out while generating the video. Please retry.",
                    "status": "error",
                },
            )

        logger.exception("Unexpected server error while processing request")
        return JSONResponse(
            status_code=500,
            content={"result": "Unexpected server error", "status": "error"},
        )
