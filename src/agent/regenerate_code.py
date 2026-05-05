from __future__ import annotations

import json
from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.graph import END
from typing_extensions import TypedDict

from agent.graph_state import State
from agent.llm import make_llm
from rag.retriever import format_evidence_block, format_foundation_block, get_foundation_chunks


llm = make_llm("openai:gpt-5.4")
DIRECT_REPAIR_LIMIT = 2
SIMPLIFY_TRIGGER_FAILURE_COUNT = DIRECT_REPAIR_LIMIT + 1
MAX_RENDER_FAILURES = 5


class CodeOutput(TypedDict):
    code: str
    scene_name: str


SYSTEM_PROMPT = """
You are fixing broken Manim Community Edition code for an educational animation.

Use:
- the runtime error,
- the previous code,
- the scene outline,
- and the retrieved evidence.

Rules:
- Preserve the intended lesson and scene flow.
- Fix only what is required, but refactor if the structure is the cause of the failure.
- Keep VoiceoverScene + GTTSService.
- Return structured output with code and scene_name only.
- Do not wrap the code in markdown fences.
""".strip()


SIMPLIFY_PROMPT = """
You are creating a simplified fallback Manim video after repeated render failures.

Top priority: generate code that actually renders successfully.

Rules:
- Preserve only the core teaching goal.
- Reduce detail aggressively if needed.
- Prefer a single compact scene with one or two visual beats.
- Use a small number of stable mobjects and straightforward animations.
- Avoid updaters, complex layouts, and dense text unless absolutely necessary.
- If VoiceoverScene or GTTSService appear likely to be causing failures, you may switch to
  a plain Scene implementation.
- It is acceptable to produce a less detailed video if it greatly improves reliability.
- Return structured output with code and scene_name only.
- Do not wrap the code in markdown fences.
""".strip()


def route_code_recovery(state: State) -> Literal["correct_code", "simplify_code", "__end__"]:
    if state.get("sandbox_error") == "No error":
        return END

    failures = state.get("render_failures", 0)
    if failures >= MAX_RENDER_FAILURES:
        return END
    if failures >= SIMPLIFY_TRIGGER_FAILURE_COUNT and not state.get("simplification_attempted", False):
        return "simplify_code"
    return "correct_code"


def correct_code(state: State) -> dict:
    evidence_blocks = [format_evidence_block(item) for item in state.get("retrieval_evidence", [])]
    foundation_block = format_foundation_block(get_foundation_chunks())
    response = llm.with_structured_output(CodeOutput).invoke(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                json.dumps(
                    {
                        "runtime_error": state.get("sandbox_error", ""),
                        "failed_code": state.get("code", ""),
                        "scene_name": state.get("scene_name", ""),
                        "scene_spec": state.get("scene_spec", {}),
                        "code_outline": state.get("code_outline", {}),
                        "foundation_block": foundation_block,
                        "evidence_blocks": evidence_blocks,
                    },
                    ensure_ascii=False,
                ),
            ),
        ],
    )
    return {
        "code": response["code"],
        "scene_name": response["scene_name"],
        "messages": [
            AIMessage(content=f"Retrying render after repair attempt {state.get('render_failures', 0)}.")
        ],
    }


def simplify_code(state: State) -> dict:
    evidence_blocks = [format_evidence_block(item) for item in state.get("retrieval_evidence", [])]
    foundation_block = format_foundation_block(get_foundation_chunks())
    response = llm.with_structured_output(CodeOutput).invoke(
        [
            ("system", SIMPLIFY_PROMPT),
            (
                "human",
                json.dumps(
                    {
                        "runtime_error": state.get("sandbox_error", ""),
                        "failed_code": state.get("code", ""),
                        "prompt": state.get("prompt", ""),
                        "topic_brief": state.get("topic_brief", {}),
                        "scene_spec": state.get("scene_spec", {}),
                        "code_outline": state.get("code_outline", {}),
                        "foundation_block": foundation_block,
                        "evidence_blocks": evidence_blocks,
                    },
                    ensure_ascii=False,
                ),
            ),
        ],
    )
    return {
        "code": response["code"],
        "scene_name": response["scene_name"],
        "simplification_attempted": True,
        "messages": [
            AIMessage(
                content=(
                    "Repeated render failures detected. Switching to a simplified fallback "
                    "scene to prioritize successful video generation."
                )
            )
        ],
    }