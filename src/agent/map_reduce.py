from __future__ import annotations

from typing_extensions import TypedDict

from langgraph.types import Send

from agent.graph_state import State
from rag.retriever import retrieve_shot_evidence


class ShotRetrievalState(TypedDict):
    shot: dict
    scene_spec: dict
    topic_brief: dict
    prompt: str


def continue_shots(state: State) -> list[Send]:
    return [
        Send(
            "get_chunks",
            {
                "shot": shot,
                "scene_spec": state["scene_spec"],
                "topic_brief": state["topic_brief"],
                "prompt": state["prompt"],
            },
        )
        for shot in state["shot_plan"]
    ]


def get_chunks(state: ShotRetrievalState) -> dict:
    shot = state["shot"]
    evidence = retrieve_shot_evidence(
        shot=shot,
        scene_spec=state["scene_spec"],
        topic_brief=state["topic_brief"],
        prompt=state["prompt"],
    )
    return {"retrieval_evidence": [evidence]}
