from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from pydantic import BaseModel
from typing import List, Dict, Any
from typing_extensions import TypedDict

from agent.fine_tune_agent.prompts.prompt_scene_plan import _prompt_scene_plan
from agent.fine_tune_agent.graph_state import IndividualScene, State

llm = init_chat_model("openai:gpt-4.1")

class IndividualScenes(TypedDict):
    IndividualScene: List[IndividualScene]
    scene_name: str
    
def scene_plan_node(state: State):
    prompt = _prompt_scene_plan.format(prompt=state["user_prompt"])
    structured_llm = llm.with_structured_output(IndividualScenes)
    response = structured_llm.invoke([
        {"role": "system", "content": prompt}
    ])
    ai_msg = AIMessage(content="Scene plan generated.")
    
    return {
        "messages": [ai_msg],
        "IndividualScene": response["IndividualScene"],
        "scene_name": response["scene_name"]
    }