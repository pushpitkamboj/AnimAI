from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from pydantic import BaseModel
from typing import Dict, Any, List
from typing_extensions import TypedDict
from agent.fine_tune_agent.prompts.prompt_scene_animation_narration import _prompt_scene_animation_narration
from agent.fine_tune_agent.graph_state import State, AnimationNarrationPlan
llm = init_chat_model("openai:gpt-4.1")

class AnimationNarrationPlans(TypedDict):
    animation_plans: List[AnimationNarrationPlan]


def animation_narration_node(state: State):
    prompt = _prompt_scene_animation_narration.format(
        IndividualScene=state["IndividualScene"],
        TeachingFrameworkPlan=state["TeachingFrameworkPlan"],
        TechnicalImplementationPlan=state["TechnicalImplementationPlan"]
    )
    structured_llm = llm.with_structured_output(AnimationNarrationPlans)
    response = structured_llm.invoke([
        {"role": "system", "content": prompt}
    ])
    ai_msg = AIMessage(content="Animation and narration plan generated.")
    return {
        "messages": [ai_msg],
        "AnimationNarrationPlan": response["animation_plans"]
    }