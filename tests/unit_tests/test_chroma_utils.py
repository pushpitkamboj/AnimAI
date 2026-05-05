import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import chroma_utils


def test_chroma_query_enabled_requires_cloud_credentials_and_embedding_key(monkeypatch) -> None:
    for env_name in (
        "CHROMA_API_KEY",
        "CHROMA_DATABASE",
        "CHROMA_TENANT",
        "CHROMA_OPENAI_API_KEY",
        "OPENAI_API_KEY",
    ):
        monkeypatch.delenv(env_name, raising=False)

    assert chroma_utils.chroma_query_enabled() is False

    monkeypatch.setenv("CHROMA_API_KEY", "cache-key")
    monkeypatch.setenv("CHROMA_DATABASE", "cache-db")
    monkeypatch.setenv("CHROMA_TENANT", "cache-tenant")
    assert chroma_utils.chroma_query_enabled() is False

    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    assert chroma_utils.chroma_query_enabled() is True


def test_chroma_openai_key_prefers_chroma_specific_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("CHROMA_OPENAI_API_KEY", "chroma-openai-key")

    assert chroma_utils._chroma_openai_api_key_env_var() == "CHROMA_OPENAI_API_KEY"
