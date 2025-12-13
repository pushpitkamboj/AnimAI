from agent.graph_state import State
from typing import Literal
from pydantic import BaseModel
from langgraph.graph import END
from langchain.chat_models import init_chat_model
from agent.graph_state import State
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
    if you get error explicitly about the azure keys not found or soemthing similar,
    change the code to use gtts
    example:
    
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService


class GTTSExample(VoiceoverScene): #whatever the name is, keep that default
    def construct(self):
        self.set_speech_service(GTTSService(lang="en", tld="com")) #USE GTTS

        circle = Circle()
        square = Square().shift(2 * RIGHT)

        with self.voiceover(text="This circle is drawn as I speak.") as tracker:
            self.play(Create(circle), run_time=tracker.duration)

        with self.voiceover(text="Let's shift it to the left 2 units.") as tracker:
            self.play(circle.animate.shift(2 * LEFT), run_time=tracker.duration)

        with self.voiceover(text="Now, let's transform it into a square.") as tracker:
            self.play(Transform(circle, square), run_time=tracker.duration)

        with self.voiceover(text="Thank you for watching."):
            self.play(Uncreate(circle))

        self.wait()

    
    this is the manim code, fix the error using manim docs.
    """
    
    structured_llm = llm.with_structured_output(output_code)
    response = structured_llm.invoke([{"role": "system", "content": prompt}] + state["messages"])
    
    return {
        "code": response.code,
        "scene_name": response.scene_name
    }