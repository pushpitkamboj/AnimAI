from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from pydantic import BaseModel
from typing import List, Dict, Any
from typing_extensions import TypedDict
from agent.fine_tune_agent.prompts.prompt_scene_technical_implementation import _prompt_scene_technical_implementation
from agent.fine_tune_agent.prompts.prompt_manim_cheatsheet import _prompt_manim_cheatsheet
from agent.fine_tune_agent.graph_state import TechnicalImplementationPlan, IndividualScene, TeachingFrameworkPlan, State

llm = init_chat_model("openai:gpt-4.1")

class TechnicalImplementationPlans(TypedDict):
    technical_scenes: List[TechnicalImplementationPlan]

def technical_implementation_node(state: State):
    prompt = _prompt_scene_technical_implementation.format(
        IndividualScene=state["IndividualScene"],
        # TeachingFrameworkPlan=state["TeachingFrameworkPlan"],
        _prompt_manim_cheatsheet=_prompt_manim_cheatsheet
    )
    structured_llm = llm.with_structured_output(TechnicalImplementationPlans)
    response = structured_llm.invoke([
        {"role": "system", "content": prompt}
    ])
    ai_msg = AIMessage(content="Technical implementation plan generated.")
    return {
        "messages": [ai_msg],
        "TechnicalImplementationPlan": response["technical_scenes"]
    }