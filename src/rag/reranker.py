from __future__ import annotations

from typing import Any


def _normalize(score: float, maximum: float) -> float:
    if maximum <= 0:
        return 0.0
    return max(score, 0.0) / maximum


def _token_overlap(expected: list[str], observed: list[str]) -> float:
    expected_set = {item.lower() for item in expected if item}
    observed_set = {item.lower() for item in observed if item}
    if not expected_set:
        return 0.0
    return len(expected_set & observed_set) / len(expected_set)


def rerank_candidates(candidates: list[dict[str, Any]], shot: dict[str, Any]) -> list[dict[str, Any]]:
    if not candidates:
        return []

    max_lexical = max(candidate.get("score_lexical", 0.0) for candidate in candidates) or 1.0
    max_dense = max(candidate.get("score_dense", 0.0) for candidate in candidates) or 1.0
    expected_symbols = shot.get("candidate_symbols", [])
    expected_patterns = shot.get("animation_patterns", [])
    visible_objects = shot.get("visible_objects", [])

    reranked: list[dict[str, Any]] = []
    for candidate in candidates:
        metadata = candidate.get("metadata", {})
        symbol = metadata.get("symbol", "")
        symbol_overlap = _token_overlap(expected_symbols, [symbol, *metadata.get("aliases", [])])
        animation_overlap = _token_overlap(
            expected_patterns,
            metadata.get("animation_patterns", []) + metadata.get("visual_patterns", []),
        )
        object_overlap = _token_overlap(
            visible_objects,
            metadata.get("keywords", []) + metadata.get("domain_tags", []),
        )
        rerank_score = (
            0.35 * _normalize(candidate.get("score_dense", 0.0), max_dense)
            + 0.30 * _normalize(candidate.get("score_lexical", 0.0), max_lexical)
            + 0.20 * symbol_overlap
            + 0.10 * animation_overlap
            + 0.05 * object_overlap
        )
        updated = dict(candidate)
        updated["score_rerank"] = round(rerank_score, 6)
        reranked.append(updated)

    return sorted(reranked, key=lambda item: item.get("score_rerank", 0.0), reverse=True)
