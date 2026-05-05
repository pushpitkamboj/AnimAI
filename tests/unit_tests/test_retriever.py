import sys
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rag.example_chunks import extract_example_chunks
import rag.retriever as retriever_module
from rag.retriever import get_foundation_chunks, retrieve_shot_evidence
from rag.synthetic_chunks import build_synthetic_symbol_chunks


@pytest.fixture(autouse=True)
def _disable_dense_retrieval(monkeypatch: pytest.MonkeyPatch) -> None:
    for env_name in ("CHROMA_API_KEY", "CHROMA_TENANT", "CHROMA_DATABASE"):
        monkeypatch.delenv(env_name, raising=False)
    monkeypatch.setattr(retriever_module, "_maybe_dense_search", lambda *args, **kwargs: [])


def test_extract_example_chunks_returns_examples() -> None:
    source_path = ROOT_DIR / "src" / "manim_docs" / "mobject_geometry_arc.py"
    chunks = extract_example_chunks(str(source_path))
    assert chunks
    assert any(chunk["metadata"].get("scene_name") for chunk in chunks)


def test_synthetic_symbol_chunks_cover_missing_core_symbols() -> None:
    chunks = build_synthetic_symbol_chunks(ROOT_DIR / "src" / "manim_docs")
    symbols = {chunk["metadata"]["symbol"] for chunk in chunks}
    expected = {
        "AnimationGroup",
        "Create",
        "FadeIn",
        "FadeOut",
        "Flash",
        "GTTSService",
        "Indicate",
        "LaggedStart",
        "MarkupText",
        "MoveAlongPath",
        "ReplacementTransform",
        "Succession",
        "Text",
        "TracedPath",
        "Transform",
        "VoiceoverScene",
        "Write",
        "always_redraw",
    }
    assert expected <= symbols


def test_retrieve_shot_evidence_returns_api_context() -> None:
    shot = {
        "shot_id": "shot_2",
        "order": 2,
        "purpose": "Plot a sine wave on axes and highlight the moving point on the curve.",
        "narration": "The point slides along the sine curve as the angle increases.",
        "continuity_from_previous": "Reuse the axes from the previous shot.",
        "visible_objects": ["axes", "sine curve", "moving point", "label"],
        "candidate_symbols": ["Axes", "ValueTracker", "always_redraw", "Dot", "Create", "Transform"],
        "animation_patterns": ["Create", "Transform", "MoveAlongPath", "LaggedStart"],
        "expected_output": "A readable graph shot with one moving point.",
        "difficulty": "medium",
        "grounded_claims": [],
        "simplifications": [],
    }
    scene_spec = {
        "title": "Sine Motion",
        "concept": "Sine wave",
        "audience": "general",
        "teaching_goal": "Show how the point traces the curve.",
    }
    topic_brief = {
        "topic_title": "Sine Wave",
        "key_facts": ["A sine wave oscillates smoothly between positive and negative values."],
        "process_steps": ["Draw axes", "Draw curve", "Move point along curve"],
    }

    evidence = retrieve_shot_evidence(shot, scene_spec, topic_brief, "visualize a sine wave")
    assert evidence["shot_id"] == "shot_2"
    assert evidence["selected_api_chunks"]
    assert {"Create", "Transform"} & set(evidence["allowed_symbols"])


def test_foundation_chunks_include_voiceover_symbols() -> None:
    chunks = get_foundation_chunks()
    symbols = {chunk["metadata"]["symbol"] for chunk in chunks}
    assert {"VoiceoverScene", "GTTSService"} <= symbols
