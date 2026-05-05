from dotenv import load_dotenv

load_dotenv()

import operator
from typing import Annotated, Literal

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class RouteInfo(TypedDict):
    route: Literal[
        "concept_only",
        "named_real_world_event",
        "named_real_world_system",
        "equation_or_derivation",
        "reaction_or_pathway",
        "mixed",
    ]
    needs_external_grounding: bool
    named_entities: list[str]
    time_sensitive: bool
    domain: Literal[
        "space",
        "physics",
        "math",
        "chemistry",
        "biology",
        "engineering",
        "general_science",
    ]
    ambiguity_notes: list[str]


class TopicBrief(TypedDict):
    topic_title: str
    factual_summary: str
    key_facts: list[str]
    quantitative_data: list[str]
    process_steps: list[str]
    visual_elements: list[str]
    spatial_relationships: list[str]
    misconceptions_to_avoid: list[str]
    narration_outline: list[str]
    recommended_visual_mode: Literal["conceptual", "quantitative", "hybrid"]
    source_registry: list[str]
    source_snippets: list[str]
    unresolved_questions: list[str]


class SceneSpec(TypedDict):
    title: str
    concept: str
    audience: str
    teaching_goal: str
    visual_style: Literal[
        "math_clean",
        "physics_diagram",
        "graph_explainer",
        "mission_walkthrough",
        "process_explainer",
        "hybrid_story",
    ]
    visual_mode: Literal["conceptual", "quantitative", "hybrid"]
    narrative_style: Literal[
        "mission_walkthrough",
        "process_explainer",
        "derivation_explainer",
        "mechanism_explainer",
        "concept_explainer",
    ]
    continuity_rules: list[str]
    banned_patterns: list[str]
    success_criteria: list[str]
    layout_strategy: list[str]


class ShotPlan(TypedDict):
    shot_id: str
    order: int
    purpose: str
    narration: str
    continuity_from_previous: str
    visible_objects: list[str]
    candidate_symbols: list[str]
    animation_patterns: list[str]
    expected_output: str
    difficulty: Literal["low", "medium", "high"]
    grounded_claims: list[str]
    simplifications: list[str]


class RetrievedChunk(TypedDict):
    chunk_id: str
    source_type: Literal["api", "example"]
    symbol: str
    score_dense: float
    score_lexical: float
    score_rerank: float
    content: str
    metadata: dict


class ShotEvidence(TypedDict):
    shot_id: str
    dense_query: str
    lexical_query: str
    selected_api_chunks: list[RetrievedChunk]
    selected_example_chunks: list[RetrievedChunk]
    rejected_candidates: list[str]
    allowed_symbols: list[str]
    notes: list[str]


class HelperFunctionSpec(TypedDict):
    name: str
    purpose: str
    inputs: list[str]
    outputs: list[str]
    dependencies: list[str]


class ShotFunctionSpec(TypedDict):
    name: str
    shot_id: str
    purpose: str
    uses_helpers: list[str]
    persistent_objects_used: list[str]
    key_symbols: list[str]


class CodeOutline(TypedDict):
    scene_name: str
    scene_class: str
    imports: list[str]
    persistent_objects: list[str]
    helper_functions: list[HelperFunctionSpec]
    shot_functions: list[ShotFunctionSpec]
    transition_rules: list[str]
    validation_checks: list[str]


class State(TypedDict):
    messages: Annotated[list, add_messages]
    prompt: str
    language: str
    animation: bool
    non_animation_reply: str
    route_info: RouteInfo
    topic_brief: TopicBrief
    scene_spec: SceneSpec
    shot_plan: Annotated[list[ShotPlan], operator.add]
    retrieval_evidence: Annotated[list[ShotEvidence], operator.add]
    code_outline: CodeOutline
    code: str
    scene_name: str
    sandbox_error: str
    video_url: str
    render_failures: int
    simplification_attempted: bool
    instructions: Annotated[list, operator.add]
    mapped_chunks: Annotated[list, operator.add]
