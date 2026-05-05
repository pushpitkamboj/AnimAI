import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest


ROOT_DIR = Path(__file__).resolve().parents[2]
WORKER_APP_PATH = ROOT_DIR / "manim-worker" / "app.py"


def _load_worker_module():
    spec = importlib.util.spec_from_file_location("animai_manim_worker_app", WORKER_APP_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["animai_manim_worker_app"] = module
    spec.loader.exec_module(module)
    return module


def test_validate_payload_accepts_valid_scene_name() -> None:
    worker = _load_worker_module()
    code, scene_name, request_id = worker._validate_payload(
        {"code": "from manim import *", "scene_name": "TestScene"}
    )
    assert code == "from manim import *"
    assert scene_name == "TestScene"
    assert request_id


def test_validate_payload_rejects_invalid_scene_name() -> None:
    worker = _load_worker_module()
    with pytest.raises(worker.HTTPException) as exc_info:
        worker._validate_payload({"code": "from manim import *", "scene_name": "../bad-scene"})

    assert exc_info.value.status_code == 400
    assert "valid Python class identifier" in exc_info.value.detail


def test_build_manim_command_uses_configured_quality_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MANIM_QUALITY_FLAG", "-qm")
    worker = _load_worker_module()

    command = worker._build_manim_command(
        Path("/tmp/manim-worker/test/scene.py"),
        "TestScene",
        Path("/tmp/manim-worker/test/media"),
    )

    assert command[:3] == ["manim", "-qm", "/tmp/manim-worker/test/scene.py"]
    assert "--disable_caching" in command


def test_create_job_returns_job_id(monkeypatch: pytest.MonkeyPatch) -> None:
    worker = _load_worker_module()
    client = TestClient(worker.app)

    with patch.object(worker, "_run_job", return_value=None):
        response = client.post(
            "/jobs",
            json={
                "scene_name": "TestScene",
                "code": "from manim import *\nclass TestScene(Scene):\n    pass",
                "request_id": "req-001",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"]
    assert body["status"] == "queued"
