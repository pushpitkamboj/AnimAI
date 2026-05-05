from __future__ import annotations

import os
from functools import lru_cache


def _chroma_openai_api_key_env_var() -> str | None:
    if os.getenv("CHROMA_OPENAI_API_KEY"):
        return "CHROMA_OPENAI_API_KEY"
    if os.getenv("OPENAI_API_KEY"):
        return "OPENAI_API_KEY"
    return None


def chroma_query_enabled() -> bool:
    required = ("CHROMA_API_KEY", "CHROMA_DATABASE", "CHROMA_TENANT")
    return all(os.getenv(name) for name in required) and _chroma_openai_api_key_env_var() is not None


@lru_cache(maxsize=1)
def get_chroma_embedding_function():
    api_key_env_var = _chroma_openai_api_key_env_var()
    if api_key_env_var is None:
        return None

    try:
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
    except ImportError:
        return None

    return OpenAIEmbeddingFunction(
        api_key_env_var=api_key_env_var,
        model_name=os.getenv("CHROMA_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
    )


def embed_texts(texts: list[str]) -> list:
    embedding_function = get_chroma_embedding_function()
    if embedding_function is None:
        return []
    return embedding_function(texts)


def get_chroma_cloud_client():
    try:
        import chromadb
    except ImportError:
        return None

    cloud_host = (os.getenv("CHROMA_HOST") or "").strip()
    client_kwargs = {
        "api_key": os.getenv("CHROMA_API_KEY"),
        "database": os.getenv("CHROMA_DATABASE"),
        "tenant": os.getenv("CHROMA_TENANT"),
    }
    if cloud_host:
        client_kwargs["cloud_host"] = cloud_host

    return chromadb.CloudClient(**client_kwargs)
