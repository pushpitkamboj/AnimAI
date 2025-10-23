from agent.graph_state import State
from typing import Literal
from pydantic import BaseModel
from langgraph.graph import END
from langchain.chat_models import init_chat_model

llm = init_chat_model("openai:gpt-4.1")


class output_code(BaseModel): 
    code: str
    scene_name: str


def is_valid_code(state: State) -> Literal["correct_code", END]:
    if state["sandbox_error"] == "No error":
        return END
    
    else:
        return "correct_code"


def correct_code(state: State): 
    prompt = f"""
    the code generated eariler has errors, see error - {state["sandbox_error"]} and the code is - {state["code"]},
    this is the manim code, fix the error using manim docs.
    """
    
    structured_llm = llm.with_structured_output(output_code)
    response = structured_llm.invoke([{"role": "system", "content": prompt}] + state["messages"])
    
    return {
        "code": response.code,
        "scene_name": response.scene_name
    }