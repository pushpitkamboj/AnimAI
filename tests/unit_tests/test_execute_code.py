import sys
from pathlib import Path
from types import SimpleNamespace


ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import agent.execute_code as execute_module


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


def test_execute_code_submits_and_polls_until_success(monkeypatch) -> None:
    monkeypatch.setenv("MANIM_WORKER_URL", "http://worker")
    monkeypatch.setenv("MANIM_WORKER_POLL_SECONDS", "5")
    monkeypatch.setenv("MANIM_WORKER_MAX_WAIT_SECONDS", "15")

    poll_responses = iter(
        [
            {"job_id": "job-1", "status": "queued"},
            {"job_id": "job-1", "status": "running"},
            {"job_id": "job-1", "status": "succeeded", "video_url": "https://cdn.test/video.mp4"},
        ]
    )
    captured = {"post": [], "get": [], "sleeps": []}

    def fake_post(url, json, timeout):
        captured["post"].append((url, json, timeout))
        return _Response(next(poll_responses))

    def fake_get(url, timeout):
        captured["get"].append((url, timeout))
        return _Response(next(poll_responses))

    monkeypatch.setattr(execute_module.requests, "post", fake_post)
    monkeypatch.setattr(execute_module.requests, "get", fake_get)
    monkeypatch.setattr(execute_module.time, "sleep", lambda seconds: captured["sleeps"].append(seconds))

    result = execute_module.execute_code({"code": "print('hi')", "scene_name": "TestScene"})

    assert result["sandbox_error"] == "No error"
    assert result["video_url"] == "https://cdn.test/video.mp4"
    assert len(captured["get"]) == 2
    assert captured["sleeps"] == [5, 5]


def test_execute_code_returns_failure_from_worker(monkeypatch) -> None:
    monkeypatch.setenv("MANIM_WORKER_URL", "http://worker")
    monkeypatch.setattr(
        execute_module.requests,
        "post",
        lambda url, json, timeout: _Response({"job_id": "job-2", "status": "queued"}),
    )
    monkeypatch.setattr(
        execute_module.requests,
        "get",
        lambda url, timeout: _Response({"job_id": "job-2", "status": "failed", "error": "Manim failed"}),
    )
    monkeypatch.setattr(execute_module.time, "sleep", lambda seconds: None)

    result = execute_module.execute_code(
        {"code": "print('hi')", "scene_name": "TestScene", "render_failures": 1}
    )

    assert result["video_url"] == ""
    assert result["sandbox_error"] == "Manim failed"
    assert result["render_failures"] == 2
