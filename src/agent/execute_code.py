from __future__ import annotations

import os
import time
from uuid import uuid4

import requests

from agent.graph_state import State
from observability.langfuse import start_langfuse_observation


def _worker_url() -> str:
    return os.getenv("MANIM_WORKER_URL", "http://localhost:8080").rstrip("/")


def _poll_interval_seconds() -> int:
    return max(1, int(os.getenv("MANIM_WORKER_POLL_SECONDS", "5")))


def _max_wait_seconds() -> int:
    return max(_poll_interval_seconds(), int(os.getenv("MANIM_WORKER_MAX_WAIT_SECONDS", "900")))


def execute_code(state: State) -> dict:
    worker_url = _worker_url()
    if not worker_url:
        return {
            "sandbox_error": "MANIM_WORKER_URL is not configured",
            "video_url": "",
            "render_failures": state.get("render_failures", 0) + 1,
        }

    request_id = str(uuid4())
    with start_langfuse_observation(
        name="execute-code",
        as_type="tool",
        input={"scene_name": state["scene_name"], "request_id": request_id},
        metadata={"worker_url": worker_url},
    ) as observation:
        trace_id = observation.trace_id if observation is not None else ""
        parent_span_id = observation.id if observation is not None else ""
        payload = {
            "code": state["code"],
            "scene_name": state["scene_name"],
            "request_id": request_id,
            "trace_id": trace_id,
            "parent_span_id": parent_span_id,
        }

        try:
            submit_response = requests.post(
                f"{worker_url}/jobs",
                json=payload,
                timeout=30,
            )
            submit_response.raise_for_status()
            submit_data = submit_response.json()
        except requests.RequestException as exc:
            if observation is not None:
                observation.update(level="ERROR", status_message=str(exc))
            return {
                "sandbox_error": f"Failed to submit render job: {exc}",
                "video_url": "",
                "render_failures": state.get("render_failures", 0) + 1,
            }

        job_id = submit_data.get("job_id", "").strip()
        if not job_id:
            if observation is not None:
                observation.update(level="ERROR", status_message="Render worker did not return a job_id")
            return {
                "sandbox_error": "Render worker did not return a job_id",
                "video_url": "",
                "render_failures": state.get("render_failures", 0) + 1,
            }

        poll_interval = _poll_interval_seconds()
        deadline = time.monotonic() + _max_wait_seconds()

        while time.monotonic() < deadline:
            try:
                status_response = requests.get(
                    f"{worker_url}/jobs/{job_id}",
                    timeout=30,
                )
                status_response.raise_for_status()
                status_data = status_response.json()
            except requests.RequestException as exc:
                if observation is not None:
                    observation.update(level="ERROR", status_message=str(exc))
                return {
                    "sandbox_error": f"Failed to poll render job {job_id}: {exc}",
                    "video_url": "",
                    "render_failures": state.get("render_failures", 0) + 1,
                }

            status = (status_data.get("status") or "").strip()
            if status == "succeeded":
                video_url = status_data.get("video_url", "")
                if observation is not None:
                    observation.update(output={"job_id": job_id, "status": status, "video_url": video_url})
                return {
                    "sandbox_error": "No error",
                    "video_url": video_url,
                    "render_failures": 0,
                }
            if status == "failed":
                error_message = status_data.get("error", "Render job failed")
                if observation is not None:
                    observation.update(
                        level="ERROR",
                        status_message=error_message,
                        output={"job_id": job_id, "status": status},
                    )
                return {
                    "sandbox_error": error_message,
                    "video_url": "",
                    "render_failures": state.get("render_failures", 0) + 1,
                }

            time.sleep(poll_interval)

        timeout_message = f"Render job {job_id} timed out after {_max_wait_seconds()} seconds"
        if observation is not None:
            observation.update(level="ERROR", status_message=timeout_message, output={"job_id": job_id})
        return {
            "sandbox_error": timeout_message,
            "video_url": "",
            "render_failures": state.get("render_failures", 0) + 1,
        }
