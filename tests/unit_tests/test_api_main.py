import sys
from contextlib import contextmanager
from pathlib import Path

import httpx
from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import api.main as main_module


@contextmanager
def _noop_propagation(**kwargs):
    yield


def test_run_pipeline_returns_504_for_upstream_read_timeout(monkeypatch) -> None:
    async def fake_ainvoke(*args, **kwargs):
        raise httpx.ReadTimeout("The read operation timed out")

    monkeypatch.setattr(main_module, "propagate_langfuse_attributes", _noop_propagation)
    monkeypatch.setattr(main_module, "_get_cached_video_url", lambda prompt: None)
    monkeypatch.setattr(main_module, "_cache_video_url", lambda prompt, video_url: None)
    monkeypatch.setattr(main_module, "get_langfuse_handler", lambda: None)
    monkeypatch.setattr(main_module.workflow_app, "ainvoke", fake_ainvoke)

    with TestClient(main_module.app) as client:
        response = client.post("/run", json={"prompt": "Animate projectile motion", "language": "en"})

    assert response.status_code == 504
    assert response.json() == {
        "result": "Upstream service timed out while generating the video. Please retry.",
        "status": "error",
    }


def test_semantic_cache_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("SEMANTIC_CACHE_ENABLED", raising=False)

    assert main_module._semantic_cache_enabled() is False
