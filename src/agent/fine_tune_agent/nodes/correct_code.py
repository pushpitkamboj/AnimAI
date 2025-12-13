from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from pydantic import BaseModel
from typing import List, Dict, Any
from typing_extensions import TypedDict

from agent.fine_tune_agent.prompts.prompt_manim_cheatsheet import _prompt_manim_cheatsheet
from agent.fine_tune_agent.prompts.correct_code_manim_methods import correct_code_manim_methods
from agent.fine_tune_agent.graph_state import IndividualScene, State
llm = init_chat_model("openai:gpt-4.1")

class ManimCode(TypedDict):
    code: str
        
def correct_code(state: State):
    prompt = correct_code_manim_methods.format(code=state["code"], sandbox_error=state["sandbox_error"], manim_docs=_prompt_manim_cheatsheet)
    
    structured_llm = llm.with_structured_output(ManimCode)
    response = structured_llm.invoke([
        {"role": "system", "content": prompt}
    ])
    ai_msg = AIMessage(content="code has been edited successfully.")
    
    return {
        "messages": [ai_msg],
        "code": response["code"]
    }