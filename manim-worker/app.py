import logging
import os
import re
import shutil
import subprocess
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Iterator
from uuid import uuid4

import boto3
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles


load_dotenv()

try:  # pragma: no cover - exercised in container runtime
    from langfuse import Langfuse as _Langfuse
    from langfuse import get_client as _get_langfuse_client
    from langfuse import propagate_attributes as _propagate_attributes
except Exception:  # pragma: no cover - local env may not have langfuse installed
    _Langfuse = None
    _get_langfuse_client = None
    _propagate_attributes = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="AnimAI Manim Worker")

TMP_DIR = Path(os.getenv("MANIM_TMP_DIR", "/tmp/manim-worker"))
PUBLISHED_DIR = TMP_DIR / "published"
MAX_CODE_BYTES = int(os.getenv("MANIM_MAX_CODE_BYTES", "300000"))
RENDER_TIMEOUT_SECONDS = int(os.getenv("MANIM_RENDER_TIMEOUT_SECONDS", "900"))
QUALITY_FLAG = os.getenv("MANIM_QUALITY_FLAG", "-ql").strip() or "-ql"
SCENE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
TRACE_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
SPAN_ID_PATTERN = re.compile(r"^[0-9a-f]{16}$")

TMP_DIR.mkdir(parents=True, exist_ok=True)
PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/published", StaticFiles(directory=str(PUBLISHED_DIR)), name="published")

_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = Lock()
_langfuse_configured = False


def _normalize_langfuse_host() -> None:
    host = (os.getenv("LANGFUSE_HOST") or "").strip()
    if host and not os.getenv("LANGFUSE_BASE_URL"):
        os.environ["LANGFUSE_BASE_URL"] = host


def _langfuse_enabled() -> bool:
    _normalize_langfuse_host()
    return bool(
        _Langfuse
        and _get_langfuse_client
        and _propagate_attributes
        and os.getenv("LANGFUSE_PUBLIC_KEY")
        and os.getenv("LANGFUSE_SECRET_KEY")
        and os.getenv("LANGFUSE_BASE_URL")
    )


def _langfuse_timeout() -> int:
    return max(5, int(os.getenv("LANGFUSE_TIMEOUT", "15")))


def _langfuse_flush_at() -> int:
    return max(1, int(os.getenv("LANGFUSE_FLUSH_AT", "64")))


def _langfuse_flush_interval() -> float:
    return max(1.0, float(os.getenv("LANGFUSE_FLUSH_INTERVAL", "2")))


def _configure_langfuse() -> None:
    global _langfuse_configured
    if _langfuse_configured or not _langfuse_enabled() or _Langfuse is None:
        return

    _Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        base_url=os.getenv("LANGFUSE_BASE_URL"),
        timeout=_langfuse_timeout(),
        flush_at=_langfuse_flush_at(),
        flush_interval=_langfuse_flush_interval(),
        environment=os.getenv("LANGFUSE_TRACING_ENVIRONMENT"),
        debug=os.getenv("LANGFUSE_DEBUG", "").lower() == "true",
    )
    _langfuse_configured = True
    logger.info(
        "Langfuse configured in worker base_url=%s timeout=%ss flush_at=%s flush_interval=%ss",
        os.getenv("LANGFUSE_BASE_URL"),
        _langfuse_timeout(),
        _langfuse_flush_at(),
        _langfuse_flush_interval(),
    )


def _current_langfuse_client():
    if not _langfuse_enabled():
        return None
    _configure_langfuse()
    return _get_langfuse_client()


@contextmanager
def _worker_trace_context(
    *,
    request_id: str,
    scene_name: str,
    trace_context: dict[str, str] | None,
) -> Iterator[Any | None]:
    client = _current_langfuse_client()
    if client is None or _propagate_attributes is None:
        yield None
        return

    with _propagate_attributes(
        session_id=request_id,
        tags=["animai", "worker", "render"],
        metadata={"service": "manim-worker", "scene_name": scene_name},
        trace_name="manim-worker-job",
    ):
        with client.start_as_current_observation(
            as_type="tool",
            name="manim-worker-job",
            input={"scene_name": scene_name, "request_id": request_id},
            metadata={"service": "manim-worker"},
            trace_context=trace_context,
        ) as observation:
            yield observation


@contextmanager
def _worker_step(
    *,
    name: str,
    input: dict[str, Any],
    metadata: dict[str, Any],
) -> Iterator[Any | None]:
    client = _current_langfuse_client()
    if client is None:
        yield None
        return

    with client.start_as_current_observation(
        as_type="tool",
        name=name,
        input=input,
        metadata=metadata,
    ) as observation:
        yield observation


def _validate_payload(payload: dict[str, Any]) -> tuple[str, str, str, str, str]:
    code = payload.get("code")
    scene_name = payload.get("scene_name")
    request_id = payload.get("request_id")
    trace_id = payload.get("trace_id")
    parent_span_id = payload.get("parent_span_id")

    if not isinstance(code, str) or not code.strip():
        raise HTTPException(status_code=400, detail="code and scene_name are required")
    if not isinstance(scene_name, str) or not scene_name.strip():
        raise HTTPException(status_code=400, detail="code and scene_name are required")
    if len(code.encode("utf-8")) > MAX_CODE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"code exceeds the maximum allowed size of {MAX_CODE_BYTES} bytes",
        )

    normalized_scene_name = scene_name.strip()
    if not SCENE_NAME_PATTERN.fullmatch(normalized_scene_name):
        raise HTTPException(
            status_code=400,
            detail="scene_name must be a valid Python class identifier",
        )

    normalized_request_id = (
        request_id.strip()
        if isinstance(request_id, str) and request_id.strip()
        else str(uuid4())
    )
    if not REQUEST_ID_PATTERN.fullmatch(normalized_request_id):
        raise HTTPException(
            status_code=400,
            detail="request_id may only contain letters, numbers, hyphens, and underscores",
        )

    normalized_trace_id = trace_id.strip() if isinstance(trace_id, str) else ""
    if normalized_trace_id and not TRACE_ID_PATTERN.fullmatch(normalized_trace_id):
        raise HTTPException(status_code=400, detail="trace_id must be a 32-character lowercase hex string")

    normalized_parent_span_id = parent_span_id.strip() if isinstance(parent_span_id, str) else ""
    if normalized_parent_span_id and not SPAN_ID_PATTERN.fullmatch(normalized_parent_span_id):
        raise HTTPException(status_code=400, detail="parent_span_id must be a 16-character lowercase hex string")

    return (
        code,
        normalized_scene_name,
        normalized_request_id,
        normalized_trace_id,
        normalized_parent_span_id,
    )


def _request_dir(request_id: str) -> Path:
    return TMP_DIR / request_id


def _local_published_base_url() -> str:
    return os.getenv("PUBLIC_MEDIA_BASE_URL", "http://localhost:8080/published").rstrip("/")


def _build_manim_command(source_file: Path, scene_name: str, media_dir: Path) -> list[str]:
    return [
        "manim",
        QUALITY_FLAG,
        str(source_file),
        scene_name,
        "--media_dir",
        str(media_dir),
        "--disable_caching",
    ]


def _find_video_path(media_dir: Path, scene_name: str) -> Path | None:
    matches = sorted(media_dir.glob(f"videos/**/{scene_name}.mp4"))
    if matches:
        return matches[-1]

    fallback_matches = sorted(media_dir.rglob(f"{scene_name}.mp4"))
    if fallback_matches:
        return fallback_matches[-1]
    return None


def _render_video(code: str, scene_name: str, request_id: str) -> Path:
    request_dir = _request_dir(request_id)
    if request_dir.exists():
        shutil.rmtree(request_dir, ignore_errors=True)
    request_dir.mkdir(parents=True, exist_ok=True)

    source_file = request_dir / "scene.py"
    source_file.write_text(code, encoding="utf-8")
    media_dir = request_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    command = _build_manim_command(source_file, scene_name, media_dir)
    logger.info("worker: running command=%s", " ".join(command))

    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=RENDER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Manim render timed out after {RENDER_TIMEOUT_SECONDS} seconds") from exc
    except subprocess.CalledProcessError as exc:
        error_output = (exc.stderr or exc.stdout or str(exc)).strip()
        raise RuntimeError(f"Manim failed: {error_output}") from exc

    video_path = _find_video_path(media_dir, scene_name)
    if video_path is None or not video_path.exists():
        raise RuntimeError("Video not generated")
    return video_path


def _upload_video(video_path: Path, scene_name: str, request_id: str, today: str) -> str:
    if os.getenv("SKIP_UPLOAD") == "1":
        target_dir = PUBLISHED_DIR / today / scene_name
        target_dir.mkdir(parents=True, exist_ok=True)
        published_path = target_dir / f"{request_id}.mp4"
        relative_path = published_path.relative_to(PUBLISHED_DIR).as_posix()
        shutil.copy2(video_path, published_path)
        return f"{_local_published_base_url()}/{relative_path}"

    account_id = os.getenv("R2_ACCOUNT_ID")
    access_key_id = os.getenv("R2_ACCESS_KEY_ID")
    secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
    bucket = os.getenv("R2_BUCKET")
    missing = [
        name
        for name, value in (
            ("R2_ACCOUNT_ID", account_id),
            ("R2_ACCESS_KEY_ID", access_key_id),
            ("R2_SECRET_ACCESS_KEY", secret_access_key),
            ("R2_BUCKET", bucket),
        )
        if not value
    ]
    if missing:
        raise RuntimeError("Missing required R2 environment variables: " + ", ".join(missing))

    key = f"manim/{today}/{scene_name}/{request_id}.mp4"
    client = boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name="auto",
    )
    client.upload_file(
        str(video_path),
        bucket,
        key,
        ExtraArgs={"ContentType": "video/mp4"},
    )

    public_base_url = os.getenv("R2_PUBLIC_BASE_URL", "").rstrip("/")
    if public_base_url:
        return f"{public_base_url}/{key}"
    return f"https://pub-{account_id}.r2.dev/{key}"


def _update_job(job_id: str, **updates: Any) -> None:
    with _jobs_lock:
        _jobs[job_id].update(updates)


def _run_job(
    job_id: str,
    code: str,
    scene_name: str,
    request_id: str,
    trace_id: str,
    parent_span_id: str,
) -> None:
    today = date.today().isoformat()
    request_dir = _request_dir(request_id)
    _update_job(job_id, status="running")
    trace_context: dict[str, str] | None = None
    if trace_id:
        trace_context = {"trace_id": trace_id}
        if parent_span_id:
            trace_context["parent_span_id"] = parent_span_id

    with _worker_trace_context(
        request_id=request_id,
        scene_name=scene_name,
        trace_context=trace_context,
    ) as observation:
            try:
                with _worker_step(
                    name="render-scene",
                    input={"scene_name": scene_name, "quality": QUALITY_FLAG},
                    metadata={"job_id": job_id},
                ) as render_observation:
                    video_path = _render_video(code, scene_name, request_id)
                    if render_observation is not None:
                        render_observation.update(output={"video_path": str(video_path)})

                with _worker_step(
                    name="upload-video",
                    input={"scene_name": scene_name},
                    metadata={"job_id": job_id},
                ) as upload_observation:
                    video_url = _upload_video(video_path, scene_name, request_id, today)
                    if upload_observation is not None:
                        upload_observation.update(output={"video_url": video_url})

                _update_job(
                    job_id,
                    status="succeeded",
                    video_url=video_url,
                    scene_name=scene_name,
                    request_id=request_id,
                )
                if observation is not None:
                    observation.update(output={"status": "succeeded", "video_url": video_url})
            except Exception as exc:
                logger.exception("worker: job failed job_id=%s scene_name=%s", job_id, scene_name)
                _update_job(job_id, status="failed", error=str(exc))
                if observation is not None:
                    observation.update(level="ERROR", status_message=str(exc), output={"status": "failed"})
            finally:
                if os.getenv("KEEP_RENDER_ARTIFACTS") != "1":
                    shutil.rmtree(request_dir, ignore_errors=True)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "quality": QUALITY_FLAG}


@app.post("/jobs")
def create_job(payload: dict[str, Any]) -> dict[str, str]:
    code, scene_name, request_id, trace_id, parent_span_id = _validate_payload(payload)
    job_id = str(uuid4())

    with _jobs_lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "scene_name": scene_name,
            "request_id": request_id,
            "video_url": "",
            "error": "",
        }

    Thread(
        target=_run_job,
        args=(job_id, code, scene_name, request_id, trace_id, parent_span_id),
        daemon=True,
    ).start()
    return {"job_id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return dict(job)
