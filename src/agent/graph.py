from langgraph.graph import StateGraph, START, END
import asyncio
from langsmith import traceable

from agent.graph_state import State
from agent.enhance_prompt import enhanced_prompt
from agent.map_reduce import get_chunks, continue_instructions
from agent.generate_code import generate_code
from agent.execute_code import execute_code
from agent.regenerate_code import is_valid_code, correct_code
from agent.analyze_user_prompt import analyze_user_prompt
from agent.analyze_user_prompt import animation_required

from langgraph.errors import GraphRecursionError
from langgraph.checkpoint.memory import InMemorySaver
memory = InMemorySaver()

graph = StateGraph(State)

graph.add_node(analyze_user_prompt)
graph.add_node(enhanced_prompt)
graph.add_node(get_chunks)
graph.add_node(generate_code)
graph.add_node(execute_code)
graph.add_node(correct_code)


graph.add_edge(START, "analyze_user_prompt")
graph.add_conditional_edges("analyze_user_prompt", animation_required)
graph.add_conditional_edges("enhanced_prompt", continue_instructions, ["get_chunks"])
graph.add_edge("get_chunks", "generate_code")
graph.add_edge("generate_code", "execute_code")
graph.add_conditional_edges("execute_code", is_valid_code)
graph.add_edge("correct_code", "execute_code")
workflow_app = graph.compile()

