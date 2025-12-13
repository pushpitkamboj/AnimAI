from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from pydantic import BaseModel
from typing import Dict, Any,List
from typing_extensions import TypedDict


from agent.fine_tune_agent.prompts.prompt_teaching_framework import _prompt_teaching_framework
from agent.fine_tune_agent.graph_state import State, TeachingFrameworkPlan
llm = init_chat_model("openai:gpt-4.1")

class TeachingFrameworkPlans(TypedDict):
    TeachingPlan: List[TeachingFrameworkPlan]

def teaching_framework_node(state: State):
    prompt = _prompt_teaching_framework.format(IndividualScene=state["IndividualScene"])
    structured_llm = llm.with_structured_output(TeachingFrameworkPlans)
    response = structured_llm.invoke([
        {"role": "system", "content": prompt}
    ])
    ai_msg = AIMessage(content="Teaching framework generated.")
    return {
        "messages": [ai_msg],
        "TeachingFrameworkPlan": response["TeachingPlan"]
    }