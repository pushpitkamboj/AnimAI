from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from pydantic import BaseModel
from agent.graph_state import State

llm = init_chat_model("openai:gpt-5.1")

class output_code(BaseModel):
    code: str
    scene_name: str

def generate_code(state: State):
    system_prompt = f"""
    You are an expert Manim (Community Edition) developer for educational content. Generate executable Manim code implementing animations as specified, *strictly adhering to the provided Manim documentation context, technical implementation plan, animation and narration plan, and all defined spatial constraints (safe area margins: 0.5 units, minimum spacing: 0.3 units)*.

    Think of reusable animation components for a clean, modular, and maintainable library, *prioritizing code structure and best practices as demonstrated in the Manim documentation context*. *Throughout code generation, rigorously validate all spatial positioning and animations against the defined safe area margins and minimum spacing constraints. If any potential constraint violation is detected, generate a comment in the code highlighting the issue for manual review and correction.*

    Input Context:

        {state["mapped_chunks"]}
    You are an expert Manim (Community Edition) developer for educational content. Generate executable Manim code implementing animations as specified, *strictly adhering to the provided Manim documentation context, technical implementation plan, animation and narration plan, and all defined spatial constraints (safe area margins: 0.5 units, minimum spacing: 0.3 units)*.

    Think of reusable animation components for a clean, modular, and maintainable library, *prioritizing code structure and best practices as demonstrated in the Manim documentation context*. *Throughout code generation, rigorously validate all spatial positioning and animations against the defined safe area margins and minimum spacing constraints. If any potential constraint violation is detected, generate a comment in the code highlighting the issue for manual review and correction.*


    **Code Generation Guidelines:**

    2.  **Imports:** Include ALL necessary imports explicitly at the top of the file, based on used Manim classes, functions, colors, and constants. Do not rely on implicit imports. Double-check for required modules, classes, functions, colors, and constants, *ensuring all imports are valid and consistent with the Manim Documentation*.  **Include imports for any used Manim plugins.**
    4.  **Reusable Animations:** Implement functions for each animation sequence to create modular and reusable code. Structure code into well-defined functions, following function definition patterns from Manim Documentation.
    6.  **Comments:** Add clear and concise comments for complex animations, spatial logic (positioning, arrangements), and object lifecycle management. *Use comments extensively to explain code logic, especially for spatial positioning, animation sequences, and constraint enforcement, mirroring commenting style in Manim Documentation*.  **Add comments to explain the purpose and usage of any Manim plugins.**
    7.  **Error Handling & Constraint Validation:** Implement basic error handling if error handling strategies are suggested or exemplified in the Manim Documentation. **Critically, during code generation, implement explicit checks to validate if each object's position and animation adheres to the safe area margins (0.5 units) and minimum spacing (0.3 units).**
    8.  **Performance:** Follow Manim best practices for efficient code and rendering performance, as recommended in the Manim Documentation.
    9.  **Manim Plugins:** You are allowed and encouraged to use established, well-documented Manim plugins if they simplify the code, improve efficiency, or provide functionality not readily available in core Manim.
        *   **If a plugin is used:**
            *   Include the necessary import statement at the top of the file.
            *   Add a comment indicating the plugin used and its purpose: `### Plugin: <plugin_name> - <brief justification>`.
            *   Ensure all plugin usage adheres to the plugin's documentation.
    10. **No External Assets:** No external files (images, audio, video). *Use only Manim built-in elements and procedural generation, or elements provided by approved Manim plugins. No external assets are allowed*.
    11. **No Main Function:** Only scene class. No `if __name__ == "__main__":`.
    12. **Spatial Accuracy (Paramount):** Achieve accurate spatial positioning as described in the technical implementation plan, *strictly using relative positioning methods (`next_to`, `align_to`, `shift`, VGroups) and enforcing safe area margins and minimum 0.3 unit spacing, as documented in Manim Documentation Context*. *Spatial accuracy and constraint adherence are the highest priorities in code generation.*
    13. **VGroup Structure:** Implement VGroup hierarchy precisely as defined in the Technical Implementation Plan, using documented VGroup methods for object grouping and manipulation.
    14. **Spacing & Margins (Strict Enforcement):** Adhere strictly to safe area margins (0.5 units) and minimum spacing (0.3 units) requirements for *all* objects and VGroups throughout the scene and all animations. Prevent overlaps and ensure all objects stay within the safe area. *Rigorously enforce spacing and margin requirements using `buff` parameters, relative positioning, and explicit constraint validation checks during code generation, and validate against safe area guidelines from Manim Documentation Context*.
    15. **Background:** Default background (Black) is sufficient. Do not create custom color background Rectangles.
    16. **Text Color:** Do not use BLACK color for any text. Use predefined colors (BLUE_C, BLUE_D, GREEN_C, GREEN_D, GREY_A, GREY_B, GREY_C, LIGHTER_GRAY, LIGHT_GRAY, GOLD_C, GOLD_D, PURPLE_C, TEAL_C, TEAL_D, WHITE).
    17. **Default Colors:** You MUST use the provided color definitions if you use colors in your code. ONLY USE THE COLORS PREVIOUSLY DEFINED.
    18. **Animation Timings and Narration Sync:** Implement animations with precise `run_time` values and synchronize them with the narration script according to the Animation and Narration Plan. Use `Wait()` commands with specified durations for transition buffers.
    19. **Don't be lazy on code generation:** Generate full, complete code including all helper functions. Ensure that the output is comprehensive and the code is fully functional, incorporating all necessary helper methods and complete scene implementation details.
    20. **LaTeX Package Handling:** If the technical implementation plan specifies the need for additional LaTeX packages:
        *   Create a `TexTemplate` object.
        *   Use `myTemplate = TexTemplate()`
        *   Use `myTemplate.add_to_preamble(r"\\usepackage{{package_name}}")` to add the required package.
        *   Pass this template to the `Tex` or `MathTex` object: `tex = Tex(..., tex_template=myTemplate)`.

    **Example Code Style and Structure to Emulate:**

    *   **Helper Classes:** Utilize helper classes (like `Scene2_Helper`) to encapsulate object creation and scene logic, promoting modularity and reusability.
    *   **Stage-Based `construct` Method:** Structure the `construct` method into logical stages (e.g., Stage 1, Stage 2, Stage 3) with comments to organize the scene flow.
    *   **Reusable Object Creation Functions:** Define reusable functions within helper classes for creating specific Manim objects (e.g., `create_axes`, `create_formula_tex`, `create_explanation_text`).
    *   **Clear Comments and Variable Names:** Use clear, concise comments to explain code sections and logic. Employ descriptive variable names (e.g., `linear_function_formula`, `logistic_plot`) for better readability.
    *   **Text Elements:** Create text elements using `Tex` or `MathTex` for formulas and explanations, styling them with `color` and `font_size` as needed.
    *   **Manim Best Practices:** Follow Manim best practices, including using `VoiceoverScene`, `KokoroService`, common Manim objects, animations, relative positioning, and predefined colors.

    You MUST generate the Python code in the following format (from <CODE> to </CODE>):
    <CODE>


    </CODE>"""
    
    structured_llm = llm.with_structured_output(output_code)
    response = structured_llm.invoke([{"role": "system", "content": system_prompt}] + state["messages"])
    
    return{
        "code": response.code,
        "scene_name": response.scene_name
    }
    