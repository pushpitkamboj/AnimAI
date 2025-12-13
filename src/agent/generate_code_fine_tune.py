from e2b import Sandbox
from dotenv import load_dotenv
import asyncio
from agent.graph_state import State
from pydantic import BaseModel
import requests
import os

load_dotenv()

class output_format(BaseModel):
    code: str
    scene_name: str
    
def generate_code_fine_tune(state: State):
    system_prompt = f'''
    you are an expert python engineer specialized in writing manim library code, write the code and also give it a scene name.
    Strict rules (must obey):

        1. Absolutely no LaTeX
        Forbidden tokens: MathTex, MathText, Tex, TexMobject, MathJax, \(, \), \[ , \], $, \frac, \pi, \theta, \mu, \sigma, \vec, \sqrt, \lim, \sum. If the user writes a formula (like a^2 + b^2 = c^2), convert it to plain text or Unicode: use Text("a² + b² = c²"). Never produce TeX code.

        2. Never generate calls that use TeX for axis tick labels

        Do not call axes.add_coordinates() or any variant of it. The default tick-label behavior internally relies on TeX and will crash the environment. Always create tick labels manually using plain text objects. Allowed safe alternatives (choose one):

        a. Manual numeric labels with Text
        Create tick labels in a loop using Text(str(value)) or DecimalNumber(value, include_sign=False, num_decimal_places=..., group_with_commas=False) — but only if you are sure it does not rely on TeX.
        Example:
        ticks = [-3, -2, -1, 0, 1, 2, 3]
        tick_labels = VGroup(*[
            Text(str(t), font_size=24).next_to(axes.coords_to_point(t, 0), DOWN, buff=0.1)
            for t in ticks
        ])
        self.add(tick_labels)

        b. Use add_numbers() safely
        If you use add_numbers, you must explicitly include label_constructor=Text.
        Example:
        axes.x_axis.add_numbers(*range(-3, 4), label_constructor=Text, font_size=24)

        c. Use Text for axis titles
        When labeling the axes themselves, use axes.get_axis_label() or Text() (e.g., Text("x-axis"), Text("y-axis")) and position them manually. If you are ever unsure whether a function triggers TeX, avoid it completely and use Text() instead.

        3. Replace any automatic numeric labels with non-TeX constructors

        Example safe pattern (preferred): create numbers manually with Text or with DecimalNumber(..., include_commas=False, num_decimal_places=...) configured to not use TeX internals. If you use DecimalNumber, pass parameters that prevent Tex-based rendering (explicitly pass label_constructor=Text when supported).

        4. Lint and forbidden patterns

        Before returning any code, run the following checks on the generated text (model must emulate this): reject or auto-rewrite any code containing the forbidden tokens listed above. Replace matched LaTeX fragments with Text(...) equivalent. Also ban: calls to Tex, TexTemplate, tex_to_svg_file, compile_tex, or any subprocess invocation referencing latex.

        5. If converting LaTeX, be conservative and explicit

        Convert \pi → pi or π (Unicode). Convert superscripts to Unicode superscripts where readable (x²) or to caret notation (x^2). Convert Greek letters to plain ASCII names when label length matters (e.g., mu, sigma) or use Unicode (μ, σ) if you prefer. Always wrap in Text("...").

        6. Error-safe axis label pattern (recommended code snippets)

        If you must add tick numbers, use one of these explicitly in generated code:
        # SAFE: manual Text ticks (recommended)
        ticks = [-3, -2, -1, 0, 1, 2, 3]
        tick_labels = VGroup(*[
            Text(str(t), font_size=24).next_to(axes.coords_to_point(t, 0), DOWN, buff=0.1)
            for t in ticks
        ])
        self.add(tick_labels)

        # SAFE: using add_numbers with a non-TeX constructor (if API supports label_constructor)
        # (Only generate this if you are confident the runtime's add_numbers accepts label_constructor)
        axes.x_axis.add_numbers(
            *range(-3, 4)
            label_constructor=Text,  # force Text, not Tex
            font_size=24
        )

        7. Do not call axes.add_coordinates(None, None)

        Do not generate axes.add_coordinates(None, None) or axes.add_coordinates(values=None, numbers=None). If using add_coordinates, always set label_constructor=Text or build tick labels manually.  
    '''

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
                {"role": "user", "content": state["prompt"]}
            ],
            "store": True,
            "temperature": 0
        }
    )
    return{
        "code": response.json()["choices"][0]["message"]["content"],
        "scene_name": "beautiful_scene"
    }