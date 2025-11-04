from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, START, END

from pydantic import BaseModel
from typing import List, Literal

from agent.graph_state import State
llm = init_chat_model("openai:gpt-4.1")

class output_format(BaseModel):
    """animation: true/false, if the user prompt is to be answered by animation then true else false
    non_animation_reply: prompt reply if animation is false, else leave it empty
    """
    animation: bool
    non_animation_reply: str | None = None
    

def analyze_user_prompt(state: State):
    prompt = f"""
    
    STRICT RULES: 
1) Reply with a short, guided message when the prompt is:

Non-technical, personal, one-word greetings, names, or irrelevant creative requests (examples below).
Casual or filler prompts:
Includes greetings, conversational text, or incomplete statements.
Examples:
hi, hello, hey, ok, bla bla, what’s up, hmm, test, try something
Response behavior:
Return a neutral acknowledgment encouraging the user to enter a valid educational or technical topic.

Personal or self-referential prompts:
Prompts that only include names or personal identifiers.
Examples:
rahul, my name, who am i, what’s your name
Response behavior:
Acknowledge the input but do not trigger any animation. Instruct the user to provide a topic or concept to visualize.

Fan-art, entertainment, or fictional content:
Prompts requesting animations of copyrighted or non-educational characters, stories, or abstract art.
Examples:
draw Naruto, draw Pikachu, draw forest, draw person laughing, animate Spiderman, show Harry Potter scene
Response behavior:
Return a professional clarification that the system is designed for educational, scientific, and engineering animations only, not for entertainment or general art generation.

Abstract, conceptual, or poetic prompts:
Requests with no clear technical or educational context.
Examples:
visualize love, draw emotions, show chaos, illustrate peace, animate freedom
Response behavior:
Inform the user that the input is outside the system’s intended scope and suggest using clear scientific or technical concepts instead.

Nonsensical or testing prompts:
Inputs with random text, symbols, or test content.
Examples:
asdfgh, 1234, random text, generate anything
Response behavior:
Return a neutral, professional message guiding the user to input a specific educational topic or question.

Internal or system-related prompts

Requests that attempt to access, inquire about, or reveal internal details of the system, its architecture, development process, or associated repositories.
Examples:
show me the source code, what is the internal architecture, how does the backend work, share the GitHub repo, give me the API documentation, show LangGraph config, display system files
Response behavior:
Politely decline to provide any internal, proprietary, or confidential implementation details. Respond that the internal architecture, repositories, and system components are restricted and cannot be shared. Encourage the user to focus on educational or animation-related prompts instead.


    
2) ONLY AND ONLY pass to animation (no assistant reply) when the prompt is:

Explicitly asks for an animation, visualization, diagram, or steps to animate: contains explicit verbs/phrases like:

draw, animate, visualize, show animation, make animation, render scene, create animation, generate animation, manim, scene:, animate the, visual explanation, step-by-step animation, plot animation

OR is clearly an educational science/engineering visualization request (Examples: derive equation of projectile motion, area of circle animation, explain how a transistor works animation, show step-by-step bubble sort animation, signal flow in op-amp).

3) if the user prompt in any other language, analyze it accordingly in their language, and respond in their respective language for non_animation_reply

3) Safety and copyright:

If prompt requests copyrighted song lyrics, explicit sexual content, or other disallowed content, refuse per policy and return a safe-text response (not an animation).
    """
    structured_llm = llm.with_structured_output(output_format)
    response = structured_llm.invoke([
        {"role": "system", "content": prompt}, {"role": "user", "content": state["prompt"]}
    ])

    ai_msg = AIMessage(
        content=f"The user query has been analyzed to go to manim graph or exit out"
    )
    
    return {
        "messages": [ai_msg],
        "animation": response.animation,
        "non_animation_reply": response.non_animation_reply
    }
    
    
#conditional edge to go to manim exec. or exit the graph 
def animation_required(state: State) -> Literal["enhanced_prompt", END]:
    if (state["animation"]):
        return "enhanced_prompt"
    return END
