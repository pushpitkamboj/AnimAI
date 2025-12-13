from agent.generate_code_fine_tune import generate_code_fine_tune
from agent.execute_code import execute_code
from langgraph.graph import StateGraph, START, END
from agent.regenerate_code_fine_tune import is_valid_code, correct_code
from langgraph.checkpoint.memory import InMemorySaver
from agent.graph_state import State

memory = InMemorySaver()

graph = StateGraph(State)

graph.add_node(generate_code_fine_tune)
graph.add_node(execute_code)
graph.add_node(correct_code)

graph.add_edge(START, "generate_code_fine_tune")
graph.add_edge("generate_code_fine_tune", "execute_code")
graph.add_conditional_edges("execute_code", is_valid_code)
graph.add_edge("correct_code", "execute_code")
workflow_app_fine_tune = graph.compile()
