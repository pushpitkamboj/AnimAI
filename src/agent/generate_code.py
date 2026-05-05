from __future__ import annotations

import ast
import json
import re
from typing import Any

from typing_extensions import TypedDict

from agent.graph_state import CodeOutline, State
from agent.llm import make_llm
from api.language_registry import get_language_name
from rag.retriever import format_evidence_block, format_foundation_block, get_foundation_chunks


llm = make_llm("openai:gpt-5.4")


class CodeOutput(TypedDict):
    code: str
    scene_name: str


OUTLINE_PROMPT = """
You are designing the code architecture for a single Manim educational scene.

You will receive:
- the user prompt,
- a grounded topic brief,
- a global scene spec,
- an ordered shot plan,
- and shot-level evidence.

Return a structured code outline with:
- scene_name
- scene_class
- imports
- persistent_objects
- helper_functions
- shot_functions
- transition_rules
- validation_checks

Requirements:
- The output must describe one coherent scene class.
- Reuse objects across shots whenever possible.
- Prefer transformations over recreating everything.
- Keep layout stable and educationally legible.
- Prefer plain-text labels via Text or MarkupText unless a numerical readout really
  needs DecimalNumber.
- Do not rely on LaTeX-heavy rendering for the primary explanation.
- The scene must inherit from VoiceoverScene and use GTTSService.
""".strip()


CODE_PROMPT = """
You are generating final Manim code for a grounded educational video.

You will receive:
- the user prompt,
- a grounded topic brief,
- a scene specification,
- an ordered shot plan,
- shot-level evidence packs,
- and a code outline.

Hard requirements:
- Generate one executable Python scene class.
- The class must inherit from VoiceoverScene.
- Configure self.set_speech_service(GTTSService(lang="{language}", tld="com")).
- All narration strings, spoken voiceover text, and user-facing on-screen labels must be
  written in the target language: {language_name}.
- If the user's prompt is in a different language, translate the final educational
  narration and visible labels into {language_name} while keeping code identifiers and
  Manim API names in English.
- Keep continuity across shots and reuse persistent objects.
- Use helper methods when the outline asks for them.
- Prefer evidence-supported Manim APIs and common CE patterns.
- Prefer Text or MarkupText for explanatory labels and formulas to keep rendering robust.
- Use DecimalNumber for changing numeric values when needed.
- Avoid unsupported custom abstractions.
- Keep the visual design clean, educational, and readable.
- Do not include markdown fences.
- Do not include if __name__ == "__main__".

Preferred API families:
- layout: VGroup, Group, next_to, arrange, to_edge, align_to, shift
- graphing: Axes, NumberPlane, FunctionGraph, ParametricFunction, DashedLine
- geometry: Circle, Dot, Line, Arrow, Arc, Polygon, Rectangle, Square
- updates: ValueTracker, always_redraw
- motion: Create, FadeIn, FadeOut, Transform, ReplacementTransform, MoveAlongPath,
  LaggedStart, Succession, AnimationGroup, Indicate, Circumscribe, Flash

Do not switch the whole scene layout abruptly unless the outline explicitly requires it.
""".strip()


FIX_PROMPT = """
You are repairing Manim code after deterministic validation failed.

Fix only the issues listed. Preserve the intended scene.
Return structured output with:
- code
- scene_name
""".strip()


def _ordered_shots(state: State) -> list[dict[str, Any]]:
    return sorted(state.get("shot_plan", []), key=lambda shot: shot["order"])


def _ordered_evidence(state: State) -> list[dict[str, Any]]:
    evidence = state.get("retrieval_evidence", [])
    shot_order = {shot["shot_id"]: shot["order"] for shot in _ordered_shots(state)}
    return sorted(evidence, key=lambda item: shot_order.get(item["shot_id"], 999))


def _outline_payload(state: State) -> str:
    payload = {
        "prompt": state.get("prompt", ""),
        "topic_brief": state.get("topic_brief", {}),
        "scene_spec": state.get("scene_spec", {}),
        "shot_plan": _ordered_shots(state),
        "evidence_summary": [
            {
                "shot_id": item["shot_id"],
                "allowed_symbols": item["allowed_symbols"],
                "notes": item["notes"],
            }
            for item in _ordered_evidence(state)
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def _code_payload(state: State) -> str:
    evidence_blocks = [format_evidence_block(item) for item in _ordered_evidence(state)]
    foundation_chunks = get_foundation_chunks()
    language = state.get("language", "en") or "en"
    payload = {
        "prompt": state.get("prompt", ""),
        "target_language": language,
        "topic_brief": state.get("topic_brief", {}),
        "scene_spec": state.get("scene_spec", {}),
        "shot_plan": _ordered_shots(state),
        "code_outline": state.get("code_outline", {}),
        "foundation_block": format_foundation_block(foundation_chunks),
        "evidence_blocks": evidence_blocks,
    }
    return json.dumps(payload, ensure_ascii=False)


def _validate_generated_code(code: str, scene_name: str) -> list[str]:
    errors: list[str] = []
    if "```" in code:
        errors.append("Code contains markdown fences.")

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [f"SyntaxError: {exc}"]

    class_names = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
    if scene_name not in class_names:
        errors.append(f"scene_name '{scene_name}' does not match any class in the code.")
    if "VoiceoverScene" not in code:
        errors.append("VoiceoverScene is missing.")
    if "GTTSService" not in code:
        errors.append("GTTSService is missing.")
    if "set_speech_service" not in code:
        errors.append("set_speech_service call is missing.")
    return errors


def generate_code_outline(state: State) -> dict:
    response = llm.with_structured_output(CodeOutline).invoke(
        [("system", OUTLINE_PROMPT), ("human", _outline_payload(state))],
    )
    return {"code_outline": response}


def generate_code(state: State) -> dict:
    language = state.get("language", "en")
    language_name = get_language_name(language)
    response = llm.with_structured_output(CodeOutput).invoke(
        [
            ("system", CODE_PROMPT.format(language=language, language_name=language_name)),
            ("human", _code_payload(state)),
        ],
    )
    code = response["code"]
    scene_name = response["scene_name"]
    validation_errors = _validate_generated_code(code, scene_name)
    if validation_errors:
        fix_response = llm.with_structured_output(CodeOutput).invoke(
            [
                ("system", FIX_PROMPT),
                (
                    "human",
                    json.dumps(
                        {
                            "errors": validation_errors,
                            "code": code,
                            "scene_name": scene_name,
                            "code_outline": state.get("code_outline", {}),
                            "scene_spec": state.get("scene_spec", {}),
                        },
                        ensure_ascii=False,
                    ),
                ),
            ],
        )
        code = fix_response["code"]
        scene_name = fix_response["scene_name"]

    code = re.sub(r"^```(?:python)?\n|\n```$", "", code.strip(), flags=re.MULTILINE)
    return {"code": code, "scene_name": scene_name}
