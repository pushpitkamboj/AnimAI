from dotenv import load_dotenv
load_dotenv()

from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from e2b_code_interpreter import Sandbox
from typing import List, Dict, Any
import operator
from typing_extensions import TypedDict, List, Dict, Any


class IndividualScene(TypedDict):
    title: str
    description: str
    purpose: str
    
class TeachingFrameworkPlan(TypedDict):
    objectives: List[str]  # Key learning goals or outcomes
    structure: List[str]   # Main content sections or flow
    engagement: List[str]  # Engagement or interaction strategies
    assessment: List[str]  # Assessment or review strategies
    notes: str             # Any additional notes or recommendations    
    
# Restore technical implementation classes
class ManimObjectConfig(TypedDict):
    name: str
    type: str
    params: Dict[str, Any]

class VGroupConfig(TypedDict):
    name: str
    members: List[str]
    purpose: str

class AnimationStep(TypedDict):
    animation_type: str
    target: str
    params: Dict[str, Any]

class TechnicalImplementationPlan(TypedDict):
    dependencies: Dict[str, Any]
    objects: List[ManimObjectConfig]
    vgroups: List[VGroupConfig]
    positioning: List[Dict[str, Any]]  # {object, method, reference, buff}
    animation_sequence: List[AnimationStep]
    code_structure: Dict[str, Any]
    safety_checks: Dict[str, Any]
    

class AnimationStrategy(TypedDict):
    pedagogical_plan: List[str]
    vgroup_transitions: List[Dict[str, Any]]
    element_animations: List[Dict[str, Any]]
    scene_flow: List[str]
    transition_buffers: List[Dict[str, Any]]
    
class NarrationSync(TypedDict):
    narration_script: List[str]  # Each string can include timing cues
    sync_strategy: str

class AnimationNarrationPlan(TypedDict):
    animation_strategy: AnimationStrategy
    narration: NarrationSync

# class OutputCodeModel(TypedDict):
#     code: str
#     scene_name: str

class State(TypedDict):
    messages: Annotated[List, add_messages]
    IndividualScene: List[IndividualScene]
    TeachingFrameworkPlan: List[TeachingFrameworkPlan]
    user_prompt: str
    TechnicalImplementationPlan: List[TechnicalImplementationPlan]
    AnimationNarrationPlan: List[AnimationNarrationPlan]
    code: str
    scene_name: str
    sandbox_error: str