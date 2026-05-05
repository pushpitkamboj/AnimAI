from __future__ import annotations

import os

from langchain.chat_models import init_chat_model


def _llm_timeout_seconds() -> float:
    return max(30.0, float(os.getenv("LLM_TIMEOUT_SECONDS", "180")))


def _llm_max_retries() -> int:
    return max(0, int(os.getenv("LLM_MAX_RETRIES", "2")))


def _llm_stream_chunk_timeout_seconds() -> float:
    return max(5.0, float(os.getenv("LLM_STREAM_CHUNK_TIMEOUT_SECONDS", "60")))


def make_llm(model_name: str):
    return init_chat_model(
        model_name,
        timeout=_llm_timeout_seconds(),
        max_retries=_llm_max_retries(),
        stream_chunk_timeout=_llm_stream_chunk_timeout_seconds(),
    )
