from __future__ import annotations

import json
from typing import Literal

from langchain_core.messages import AIMessage
from typing_extensions import TypedDict

from agent.graph_state import SceneSpec, ShotPlan, State
from agent.llm import make_llm


llm = make_llm("openai:gpt-5.4")


class PlannerOutput(TypedDict):
    scene_spec: SceneSpec
    shot_plan: list[ShotPlan]


SYSTEM_PROMPT = """
You are planning a single educational Manim video scene for math, science, engineering,
and real-world explainers.

Inputs:
- the user prompt,
- a route classification,
- a factual topic brief.

Your job is to turn that into:
1. one global scene specification,
2. four to eight dependent shots in order.

Hard rules:
- Build a single coherent scene, not disconnected clips.
- Each shot must build on previous shots unless it is the opening shot.
- Preserve object identity whenever possible.
- Prefer transformations over clearing and recreating everything.
- Every shot must be visually legible and teach one main idea.
- Every shot must include a short narration line in plain language.
- Use real Manim candidate symbol names when confident.
- Do not confidently invent custom Manim classes.
- For open-world grounded prompts, keep the video faithful to the supplied facts.
- If exact scale would be educationally harmful, use hybrid or conceptual mode and state
  the simplification.

Style guidance:
- math_clean: persistent axes, labels, progressive reveal
- physics_diagram: diagram first, vectors second, motion third
- graph_explainer: persistent axes, one curve focus at a time
- mission_walkthrough: phase labels, trajectory panel, craft close-up when needed
- process_explainer: pipeline or mechanism flow with persistent step labels
- hybrid_story: mix quantitative and schematic views intentionally

Candidate symbols should include both mobjects and animations when relevant, e.g.
Axes, NumberPlane, Circle, Dot, Line, Arrow, DashedLine, Arc, FunctionGraph, VGroup,
Text, DecimalNumber, ValueTracker, always_redraw, Create, FadeIn, FadeOut, Transform,
ReplacementTransform, MoveAlongPath, AnimationGroup, Succession, LaggedStart,
Circumscribe, Indicate, Flash, Rotate.

Avoid:
- abrupt full-scene resets,
- overcrowded text,
- more than two simultaneous moving focal elements,
- unsupported factual claims,
- visual clutter that makes the concept harder to follow.
""".strip()


def plan_video(state: State) -> dict:
    response = llm.with_structured_output(PlannerOutput).invoke(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                json.dumps(
                    {
                        "prompt": state["prompt"],
                        "route_info": state["route_info"],
                        "topic_brief": state["topic_brief"],
                    },
                    ensure_ascii=False,
                ),
            ),
        ],
    )

    scene_spec: SceneSpec = response["scene_spec"]
    shot_plan: list[ShotPlan] = sorted(response["shot_plan"], key=lambda item: item["order"])
    shot_summary = "\n".join(f"{shot['order']}. {shot['purpose']}" for shot in shot_plan)
    return {
        "messages": [AIMessage(content=f"Planned scene:\n{shot_summary}")],
        "scene_spec": scene_spec,
        "shot_plan": shot_plan,
    }
