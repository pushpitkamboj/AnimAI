from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from agent.analyze_user_prompt import analyze_user_prompt, animation_required
from agent.generate_code import generate_code, generate_code_outline
from agent.graph_state import State
from agent.map_reduce import continue_shots, get_chunks
from agent.plan_video import plan_video
from agent.regenerate_code import correct_code, route_code_recovery, simplify_code
from agent.research_router import route_prompt_for_grounding
from agent.research_topic import build_topic_brief
from agent.execute_code import execute_code


graph = StateGraph(State)

graph.add_node("analyze_user_prompt", analyze_user_prompt)
graph.add_node("route_prompt_for_grounding", route_prompt_for_grounding)
graph.add_node("build_topic_brief", build_topic_brief)
graph.add_node("plan_video", plan_video)
graph.add_node(
    "get_chunks",
    get_chunks,
    retry_policy=RetryPolicy(max_attempts=3, initial_interval=1.0, backoff_factor=2.0),
)
graph.add_node("generate_code_outline", generate_code_outline)
graph.add_node("generate_code", generate_code)
graph.add_node("correct_code", correct_code)
graph.add_node("simplify_code", simplify_code)
graph.add_node("execute_code", execute_code)


graph.add_edge(START, "analyze_user_prompt")
graph.add_conditional_edges(
    "analyze_user_prompt",
    animation_required,
    {"route_prompt_for_grounding", END},
)
graph.add_edge("route_prompt_for_grounding", "build_topic_brief")
graph.add_edge("build_topic_brief", "plan_video")
graph.add_conditional_edges("plan_video", continue_shots)
graph.add_edge("get_chunks", "generate_code_outline")
graph.add_edge("generate_code_outline", "generate_code")
graph.add_edge("generate_code", "execute_code")
graph.add_conditional_edges(
    "execute_code",
    route_code_recovery,
    {END: END, "correct_code": "correct_code", "simplify_code": "simplify_code"},
)
graph.add_edge("correct_code", "execute_code")
graph.add_edge("simplify_code", "execute_code")

memory = InMemorySaver()
workflow_app = graph.compile(checkpointer=memory)
