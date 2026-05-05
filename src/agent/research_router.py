from __future__ import annotations

from typing import Literal

from langchain_core.messages import AIMessage

from agent.graph_state import RouteInfo, State
from agent.llm import make_llm


llm = make_llm("openai:gpt-5.4")


SYSTEM_PROMPT = """
You are routing educational animation prompts before planning and retrieval.

Your task is to classify whether the prompt can be handled from general conceptual
knowledge, or whether it needs external factual grounding because it references a
real-world named entity, process, event, system, recent topic, or time-sensitive fact.

Rules:
- Use needs_external_grounding=true for named missions, named products, named events,
  recent or latest topics, current scientific developments, real-world systems, named
  biological pathways, named reactions, or historical episodes where exact facts matter.
- Use concept_only only when the user is asking about a generic concept that can be
  explained without looking up current or named external facts.
- time_sensitive=true if the prompt includes recent/current/latest/today or references
  an entity whose status or timeline could have changed.
- named_entities should capture important proper nouns or canonical topic names.
- ambiguity_notes should mention under-specified parts of the prompt that may force a
  higher-level conceptual treatment.
""".strip()


def route_prompt_for_grounding(state: State) -> dict:
    prompt = state["prompt"]
    response = llm.with_structured_output(RouteInfo).invoke(
        [("system", SYSTEM_PROMPT), ("human", prompt)],
    )

    route_info: RouteInfo = response
    summary = (
        f"Route: {route_info['route']}; domain: {route_info['domain']}; "
        f"external grounding: {route_info['needs_external_grounding']}."
    )

    return {
        "messages": [AIMessage(content=summary)],
        "route_info": route_info,
    }
