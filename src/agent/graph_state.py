from dotenv import load_dotenv
load_dotenv()

from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from e2b_code_interpreter import Sandbox
from typing import List, Dict, Any
import operator

class State(TypedDict):
    messages: Annotated[list, add_messages]
    prompt: str
    code: str
    instructions: Annotated[list, operator.add]
    mapped_chunks: Annotated[list, operator.add]
    sandbox_error: str
    video_url: str
    scene_name: str
    animation: bool
    non_animation_reply: str