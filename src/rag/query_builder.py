from __future__ import annotations

from typing import Any


EXPANSION_MAP = {
    "graph": ["Axes", "NumberPlane", "FunctionGraph", "ParametricFunction"],
    "label": ["Text", "MarkupText", "DecimalNumber"],
    "move point on curve": ["MoveAlongPath", "always_redraw", "ValueTracker"],
    "highlight relation": ["Indicate", "Circumscribe", "Flash", "FadeToColor"],
    "compare two states": ["Transform", "ReplacementTransform", "FadeTransform"],
    "trajectory": ["Axes", "Line", "Arc", "Dot", "TracedPath"],
    "timeline": ["Line", "Dot", "Text", "VGroup", "LaggedStart"],
}


def _expand_terms(values: list[str]) -> list[str]:
    expanded: list[str] = []
    for value in values:
        lowered = value.lower()
        expanded.append(value)
        for trigger, additions in EXPANSION_MAP.items():
            if trigger in lowered:
                expanded.extend(additions)

    deduped: list[str] = []
    seen: set[str] = set()
    for item in expanded:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


def build_shot_queries(
    shot: dict[str, Any],
    scene_spec: dict[str, Any],
    topic_brief: dict[str, Any],
    prompt: str,
) -> tuple[str, str]:
    visible_objects = shot.get("visible_objects", [])
    candidate_symbols = _expand_terms(shot.get("candidate_symbols", []))
    animation_patterns = _expand_terms(shot.get("animation_patterns", []))
    factual_hints = topic_brief.get("key_facts", [])[:4]
    process_hints = topic_brief.get("process_steps", [])[:3]

    dense_query = "\n".join(
        [
            f"Prompt: {prompt}",
            f"Goal: {shot.get('purpose', '')}",
            f"Continuity: {shot.get('continuity_from_previous', '')}",
            f"Visible objects: {', '.join(visible_objects)}",
            f"Need Manim APIs for: {', '.join(candidate_symbols)}",
            f"Animation patterns: {', '.join(animation_patterns)}",
            f"Expected output: {shot.get('expected_output', '')}",
            f"Relevant facts: {' | '.join(factual_hints)}",
            f"Relevant process: {' | '.join(process_hints)}",
            f"Visual style: {scene_spec.get('visual_style', '')}",
        ]
    ).strip()

    lexical_tokens = [
        *candidate_symbols,
        *animation_patterns,
        *visible_objects,
        scene_spec.get("visual_style", ""),
        scene_spec.get("narrative_style", ""),
        *shot.get("grounded_claims", []),
    ]
    lexical_query = " ".join(token for token in lexical_tokens if token).strip()
    return dense_query, lexical_query
