from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Iterator

try:  # pragma: no cover - exercised in container runtime
    from langfuse import Langfuse as _Langfuse
    from langfuse import get_client as _get_client
    from langfuse import propagate_attributes as _propagate_attributes
    from langfuse.langchain import CallbackHandler as _CallbackHandler
except Exception:  # pragma: no cover - local env may not have langfuse installed
    _Langfuse = None
    _get_client = None
    _propagate_attributes = None
    _CallbackHandler = None


logger = logging.getLogger(__name__)
_client_configured = False


def _normalize_langfuse_host() -> None:
    host = (os.getenv("LANGFUSE_HOST") or "").strip()
    if host and not os.getenv("LANGFUSE_BASE_URL"):
        os.environ["LANGFUSE_BASE_URL"] = host


def langfuse_enabled() -> bool:
    _normalize_langfuse_host()
    return bool(
        _Langfuse
        and _get_client
        and _CallbackHandler
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


def configure_langfuse() -> None:
    global _client_configured
    if _client_configured or not langfuse_enabled() or _Langfuse is None:
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
    _client_configured = True
    logger.info(
        "Langfuse configured base_url=%s timeout=%ss flush_at=%s flush_interval=%ss",
        os.getenv("LANGFUSE_BASE_URL"),
        _langfuse_timeout(),
        _langfuse_flush_at(),
        _langfuse_flush_interval(),
    )


def auth_check_langfuse() -> bool:
    if not langfuse_enabled():
        return False

    configure_langfuse()
    client = _get_client()
    try:
        return bool(client.auth_check())
    except Exception:
        logger.exception("Langfuse auth_check failed")
        return False


def get_langfuse_client():
    if not langfuse_enabled():
        return None
    configure_langfuse()
    return _get_client()


def get_langfuse_handler():
    if not langfuse_enabled():
        return None
    configure_langfuse()
    return _CallbackHandler()


@contextmanager
def propagate_langfuse_attributes(
    *,
    session_id: str | None = None,
    user_id: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    trace_name: str | None = None,
    as_baggage: bool = False,
) -> Iterator[None]:
    if not langfuse_enabled() or _propagate_attributes is None:
        yield
        return

    kwargs: dict[str, Any] = {}
    if session_id:
        kwargs["session_id"] = session_id
    if user_id:
        kwargs["user_id"] = user_id
    if tags:
        kwargs["tags"] = tags
    if metadata:
        kwargs["metadata"] = metadata
    if trace_name:
        kwargs["trace_name"] = trace_name
    if as_baggage:
        kwargs["as_baggage"] = True

    if not kwargs:
        yield
        return

    with _propagate_attributes(**kwargs):
        yield


@contextmanager
def start_langfuse_observation(
    *,
    name: str,
    as_type: str = "span",
    input: Any | None = None,
    metadata: dict[str, Any] | None = None,
    trace_context: dict[str, str] | None = None,
) -> Iterator[Any | None]:
    client = get_langfuse_client()
    if client is None:
        yield None
        return

    kwargs: dict[str, Any] = {"as_type": as_type, "name": name}
    if input is not None:
        kwargs["input"] = input
    if metadata:
        kwargs["metadata"] = metadata
    if trace_context:
        kwargs["trace_context"] = trace_context

    with client.start_as_current_observation(**kwargs) as observation:
        yield observation
