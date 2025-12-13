from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage

from agent.fine_tune_agent.prompts.prompt_code_generation import _prompt_code_generation
from agent.fine_tune_agent.prompts.prompt_manim_cheatsheet import _prompt_manim_cheatsheet
from agent.fine_tune_agent.graph_state import State
import asyncio
from e2b import Sandbox
import requests
import os
from typing_extensions import TypedDict, List, Dict, Any

# llm = init_chat_model("openai:gpt-4.1")
class IndividualScene(TypedDict):
    title: str
    description: str
    purpose: str

def generate_code_node(state: State):
    # print("individual scene code ---", state["IndividualScene"])
    print(state)
    system_prompt = _prompt_code_generation.format(
        IndividualScene=state["IndividualScene"],
        # TeachingFrameworkPlan=state["TeachingFrameworkPlan"],
        TechnicalImplementationPlan=state["TechnicalImplementationPlan"],
        # AnimationNarrationPlan=state["AnimationNarrationPlan"],
        ManimCodeCheatsheet = _prompt_manim_cheatsheet
        )
    
    response = requests.post(
            "https://app.openpipe.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.environ['OPENPIPE_API_KEY']}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openpipe:vectora",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": state["user_prompt"]}
                ],
                "store": True,
                "temperature": 0
            }
        )
    
    return{
            "code": response.json()["choices"][0]["message"]["content"],
        }
