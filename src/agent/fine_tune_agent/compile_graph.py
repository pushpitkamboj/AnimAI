from langgraph.graph import StateGraph, START, END
from agent.fine_tune_agent.nodes.scene_plan import scene_plan_node
from agent.fine_tune_agent.nodes.teaching_framework import teaching_framework_node
from agent.fine_tune_agent.nodes.technical_implementation import technical_implementation_node
from agent.fine_tune_agent.nodes.scene_animation_narration import animation_narration_node
from agent.fine_tune_agent.nodes.generate_code import generate_code_node
from agent.fine_tune_agent.nodes.execute_code import execute_code
from agent.fine_tune_agent.graph_state import State
from agent.fine_tune_agent.nodes.correct_code import correct_code

from typing import Literal
# Initialize the graph with the State TypedDict
graph = StateGraph(State)



def is_valid_code(state: State) -> Literal["correct_code", END]:
    if state["sandbox_error"] == "No error":
        return END
    
    else:
        return "correct_code"
    
    
graph.add_node("scene_plan", scene_plan_node)
# graph.add_node("teaching_framework", teaching_framework_node)
graph.add_node("technical_implementation", technical_implementation_node)
# graph.add_node("animation_narration", animation_narration_node)
graph.add_node("generate_code", generate_code_node)
graph.add_node("execute_code", execute_code)
graph.add_node("correct_code", correct_code)

graph.add_edge(START, "scene_plan")
# graph.add_edge("scene_plan", "teaching_framework")
# graph.add_edge("teaching_framework", "technical_implementation")
graph.add_edge("scene_plan", "technical_implementation")
graph.add_edge("technical_implementation", "generate_code")
# graph.add_edge("animation_narration", "generate_code")
graph.add_edge("generate_code", "execute_code")

graph.add_conditional_edges("execute_code", is_valid_code)
graph.add_edge("correct_code", "execute_code")

# Compile the workflow



# graph.add_node(execute_code)
# graph.add_edge(START, "execute_code")
workflow_app_fine_tune2 = graph.compile()
    