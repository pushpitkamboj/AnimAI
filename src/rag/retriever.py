from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from chroma_utils import chroma_query_enabled, embed_texts, get_chroma_cloud_client
from rag.chunks import chunking
from rag.example_chunks import extract_example_chunks
from rag.query_builder import build_shot_queries
from rag.reranker import rerank_candidates
from rag.synthetic_chunks import build_synthetic_symbol_chunks


DOCS_DIR = Path(__file__).resolve().parents[1] / "manim_docs"
API_COLLECTION_NAME = "manim_source_code"
FOUNDATION_SYMBOLS = ["VoiceoverScene", "GTTSService"]

try:
    from rank_bm25 import BM25Okapi
except ImportError:  # pragma: no cover
    BM25Okapi = None


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z_][A-Za-z0-9_.+-]*", text)]


def _doc_url_for_module(module_name: str) -> str:
    return f"https://docs.manim.community/en/stable/reference/manim.{module_name}.html"


def _candidate_from_chunk(
    chunk: dict[str, Any],
    score_lexical: float = 0.0,
    score_dense: float = 0.0,
) -> dict[str, Any]:
    metadata = dict(chunk["metadata"])
    return {
        "chunk_id": chunk["id"],
        "source_type": metadata.get("source_type", "api"),
        "symbol": metadata.get("symbol", metadata.get("scene_name", chunk["id"])),
        "score_dense": float(score_dense),
        "score_lexical": float(score_lexical),
        "score_rerank": 0.0,
        "content": chunk["content"],
        "metadata": metadata,
    }


@lru_cache(maxsize=1)
def _load_api_chunks() -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for source_path in sorted(DOCS_DIR.glob("*.py")):
        parent_chunks, child_chunks = chunking(str(source_path), _doc_url_for_module(source_path.stem))
        for chunk in [*parent_chunks, *child_chunks]:
            chunk["metadata"] = {
                "source_type": "api",
                "chunk_kind": chunk.get("type", "").lower(),
                "symbol": chunk.get("id", ""),
                "parent_symbol": chunk.get("parent_id"),
                "children_symbols": chunk.get("children_ids", []),
                "keywords": [chunk.get("id", ""), chunk.get("type", ""), source_path.stem],
                "aliases": [chunk.get("id", ""), chunk.get("method_name", ""), source_path.stem],
                "doc_summary": chunk.get("content", "")[:300],
                "file_path": chunk.get("file_path", ""),
                "animation_patterns": [],
                "visual_patterns": [],
            }
            chunks.append(chunk)
    chunks.extend(build_synthetic_symbol_chunks(DOCS_DIR))
    return chunks


@lru_cache(maxsize=1)
def _load_example_chunks() -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for source_path in sorted(DOCS_DIR.glob("*.py")):
        chunks.extend(extract_example_chunks(str(source_path)))
    return chunks


@lru_cache(maxsize=1)
def _api_symbol_index() -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for chunk in _load_api_chunks():
        keys = [chunk["metadata"].get("symbol", ""), *chunk["metadata"].get("aliases", [])]
        for key in keys:
            normalized = key.lower()
            if not normalized:
                continue
            index.setdefault(normalized, []).append(chunk)
    return index


@lru_cache(maxsize=1)
def _api_chunk_index() -> dict[str, dict[str, Any]]:
    return {chunk["id"]: chunk for chunk in _load_api_chunks()}


@lru_cache(maxsize=1)
def _api_bm25():
    chunks = _load_api_chunks()
    corpus = [
        _tokenize(
            " ".join(
                [
                    chunk["metadata"].get("symbol", ""),
                    " ".join(chunk["metadata"].get("aliases", [])),
                    chunk["metadata"].get("doc_summary", ""),
                    " ".join(chunk["metadata"].get("keywords", [])),
                    chunk["content"],
                ]
            )
        )
        for chunk in chunks
    ]
    if BM25Okapi is None:
        return chunks, corpus, None
    return chunks, corpus, BM25Okapi(corpus)


@lru_cache(maxsize=1)
def _example_bm25():
    chunks = _load_example_chunks()
    corpus = [
        _tokenize(
            " ".join(
                [
                    chunk["metadata"].get("scene_name", ""),
                    " ".join(chunk["metadata"].get("domain_tags", [])),
                    " ".join(chunk["metadata"].get("visual_patterns", [])),
                    " ".join(chunk["metadata"].get("symbols_used", [])),
                    chunk["content"],
                ]
            )
        )
        for chunk in chunks
    ]
    if BM25Okapi is None:
        return chunks, corpus, None
    return chunks, corpus, BM25Okapi(corpus)


def _bm25_search(query: str, example: bool = False, limit: int = 8) -> list[dict[str, Any]]:
    chunks, corpus, engine = _example_bm25() if example else _api_bm25()
    tokens = _tokenize(query)
    if not tokens:
        return []

    if engine is None:
        scored: list[tuple[float, dict[str, Any]]] = []
        token_set = set(tokens)
        for chunk, chunk_tokens in zip(chunks, corpus):
            overlap = len(token_set & set(chunk_tokens))
            if overlap > 0:
                scored.append((float(overlap), chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [_candidate_from_chunk(chunk, score_lexical=score) for score, chunk in scored[:limit]]

    scores = engine.get_scores(tokens)
    ranked = sorted(zip(scores, chunks), key=lambda item: item[0], reverse=True)
    return [
        _candidate_from_chunk(chunk, score_lexical=float(score))
        for score, chunk in ranked[:limit]
        if score > 0
    ]


def _exact_symbol_matches(symbols: list[str]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    seen: set[str] = set()
    index = _api_symbol_index()
    for symbol in symbols:
        for chunk in index.get(symbol.lower(), []):
            if chunk["id"] in seen:
                continue
            seen.add(chunk["id"])
            matches.append(_candidate_from_chunk(chunk, score_lexical=10.0))
    return matches


def _maybe_dense_search(query: str, limit: int = 4) -> list[dict[str, Any]]:
    if not chroma_query_enabled():
        return []

    client = get_chroma_cloud_client()
    if client is None:
        return []

    try:
        query_embeddings = embed_texts([query])
        if not query_embeddings:
            return []
        collection = client.get_collection(name=API_COLLECTION_NAME)
        result = collection.query(query_embeddings=query_embeddings, n_results=limit)
    except Exception:
        return []

    dense_results: list[dict[str, Any]] = []
    rows = zip(
        result.get("ids", [[]])[0],
        result.get("documents", [[]])[0],
        result.get("metadatas", [[]])[0],
        result.get("distances", [[]])[0],
    )
    for chunk_id, document, metadata, distance in rows:
        dense_results.append(
            {
                "chunk_id": chunk_id,
                "source_type": (metadata or {}).get("source_type", "api"),
                "symbol": (metadata or {}).get("symbol", chunk_id),
                "score_dense": 0.0 if distance is None else max(0.0, 1.0 - float(distance)),
                "score_lexical": 0.0,
                "score_rerank": 0.0,
                "content": document,
                "metadata": metadata or {},
            }
        )
    return dense_results


def _dedupe_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        key = candidate["chunk_id"]
        if key not in merged:
            merged[key] = dict(candidate)
            continue
        merged[key]["score_dense"] = max(
            merged[key].get("score_dense", 0.0),
            candidate.get("score_dense", 0.0),
        )
        merged[key]["score_lexical"] = max(
            merged[key].get("score_lexical", 0.0),
            candidate.get("score_lexical", 0.0),
        )
    return list(merged.values())


def _expand_neighbors(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expanded = list(candidates)
    seen = {candidate["chunk_id"] for candidate in candidates}
    chunk_index = _api_chunk_index()

    for candidate in list(candidates):
        parent_symbol = candidate.get("metadata", {}).get("parent_symbol")
        if parent_symbol and parent_symbol in chunk_index and parent_symbol not in seen:
            seen.add(parent_symbol)
            expanded.append(_candidate_from_chunk(chunk_index[parent_symbol], score_lexical=1.0))
    return expanded


def _select_api_chunks(
    reranked_api: list[dict[str, Any]],
    exact_matches: list[dict[str, Any]],
    limit: int = 6,
) -> list[dict[str, Any]]:
    exact_ids = {candidate["chunk_id"] for candidate in exact_matches}
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    for candidate in reranked_api:
        if candidate["chunk_id"] not in exact_ids:
            continue
        seen.add(candidate["chunk_id"])
        selected.append(candidate)
        if len(selected) >= limit:
            return selected

    for candidate in reranked_api:
        if candidate["chunk_id"] in seen:
            continue
        seen.add(candidate["chunk_id"])
        selected.append(candidate)
        if len(selected) >= limit:
            break

    return selected


def format_evidence_block(evidence: dict[str, Any]) -> str:
    lines = [
        f"## Shot {evidence['shot_id']}",
        f"Dense query: {evidence['dense_query']}",
        f"Lexical query: {evidence['lexical_query']}",
        f"Allowed symbols: {', '.join(evidence['allowed_symbols'])}",
        "",
        "### API Evidence",
    ]
    for index, chunk in enumerate(evidence["selected_api_chunks"], start=1):
        lines.extend([f"{index}. {chunk['symbol']} (score={chunk['score_rerank']:.3f})", chunk["content"][:900], ""])
    lines.append("### Example Evidence")
    for index, chunk in enumerate(evidence["selected_example_chunks"], start=1):
        lines.extend([f"{index}. {chunk['symbol']} (score={chunk['score_rerank']:.3f})", chunk["content"][:700], ""])
    if evidence["notes"]:
        lines.append("Notes:")
        lines.extend(f"- {note}" for note in evidence["notes"])
    return "\n".join(lines).strip()


def get_foundation_chunks(symbols: list[str] | None = None) -> list[dict[str, Any]]:
    requested_symbols = symbols or FOUNDATION_SYMBOLS
    chunks = _exact_symbol_matches(requested_symbols)
    return sorted(
        chunks,
        key=lambda chunk: (
            0 if chunk["metadata"].get("symbol") in requested_symbols else 1,
            chunk["metadata"].get("symbol", ""),
        ),
    )


def format_foundation_block(chunks: list[dict[str, Any]]) -> str:
    lines = ["## Foundation Evidence"]
    for index, chunk in enumerate(chunks, start=1):
        lines.extend([f"{index}. {chunk['metadata'].get('symbol', chunk['symbol'])}", chunk["content"][:900], ""])
    return "\n".join(lines).strip()


def retrieve_shot_evidence(
    shot: dict[str, Any],
    scene_spec: dict[str, Any],
    topic_brief: dict[str, Any],
    prompt: str,
) -> dict[str, Any]:
    dense_query, lexical_query = build_shot_queries(shot, scene_spec, topic_brief, prompt)
    exact_matches = _exact_symbol_matches(shot.get("candidate_symbols", []))
    api_candidates = _bm25_search(lexical_query, example=False, limit=12)
    example_candidates = _bm25_search(lexical_query, example=True, limit=8)
    dense_candidates = _maybe_dense_search(dense_query, limit=5)

    combined_api = _expand_neighbors(_dedupe_candidates([*exact_matches, *api_candidates, *dense_candidates]))
    reranked_api = rerank_candidates(combined_api, shot)
    reranked_examples = rerank_candidates(_dedupe_candidates(example_candidates), shot)

    selected_api = _select_api_chunks(reranked_api, exact_matches, limit=6)
    selected_examples = reranked_examples[:3]
    allowed_symbols = sorted(
        {
            chunk["metadata"].get("symbol", chunk["symbol"])
            for chunk in selected_api
            if chunk["metadata"].get("symbol")
        }
    )

    notes: list[str] = []
    if not exact_matches:
        notes.append("No exact API symbol match was found; retrieval relied on lexical/context matches.")
    if shot.get("difficulty") in {"medium", "high"} and not selected_examples:
        notes.append("No example chunks were retrieved for this medium/high difficulty shot.")

    rejected_candidates = [candidate["symbol"] for candidate in reranked_api[6:10]]
    return {
        "shot_id": shot["shot_id"],
        "dense_query": dense_query,
        "lexical_query": lexical_query,
        "selected_api_chunks": selected_api,
        "selected_example_chunks": selected_examples,
        "rejected_candidates": rejected_candidates,
        "allowed_symbols": allowed_symbols,
        "notes": notes,
    }
