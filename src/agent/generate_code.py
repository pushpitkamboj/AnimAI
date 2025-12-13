from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from pydantic import BaseModel
from agent.graph_state import State

llm = init_chat_model("openai:gpt-4.1")

class output_code(BaseModel):
    code: str
    scene_name: str

def generate_code(state: State):
    system_prompt = f"""
    You are an expert Manim (Community Edition) developer for educational content. Generate executable Manim code implementing animations as specified, *strictly adhering to the provided Manim documentation context, technical implementation plan, and all defined spatial constraints (safe area margins: 0.5 units, minimum spacing: 0.3 units)*.
Think of reusable animation components for a clean, modular, and maintainable library, *prioritizing code structure and best practices as demonstrated in the Manim documentation context*. *Throughout code generation, rigorously validate all spatial positioning and animations against the defined safe area margins and minimum spacing constraints. If any potential constraint violation is detected, generate a comment in the code highlighting the issue for manual review and correction.*


input context -
chunks of manim  to be implemented = {state["mapped_chunks"]}

NOTE THE GUIDELINES


GUIDELINE 1 - MANTAIN THE SPATIAL AND VISUAL AESTHETICS ALONG WITH SYNC TIMING
**Spatial Constraints (Strictly Enforced Throughout Animations):**
*   **Safe area margins:** 0.5 units. *Maintain objects and VGroups within margins.*
*   **Minimum spacing:** 0.3 units. *Ensure minimum spacing between all objects and VGroups.*

**Animation Timing and Pacing Requirements:**
*   Specify `run_time` for all animations.
*   Use `Wait()` for transition buffers, specifying durations and **pedagogical purpose**.
*   Coordinate animation timings with narration cues for synchronized pedagogical presentation.

**Visual Flow and Pedagogical Clarity:**
*   Ensure animations create a clear and logical visual flow, **optimized for learning and concept understanding.**
*   Use animation pacing and transition buffers to visually separate ideas and **enhance pedagogical clarity.**
*   Maintain spatial coherence for predictable and understandable animations, strictly adhering to spatial constraints.

**Diagrams/Sketches (Optional but Highly Recommended for Complex Scenes):**
*   For complex animations, include diagrams/sketches to visualize animation flow and object movements. This aids clarity and reduces errors.

Your plan must demonstrate a strong understanding of pedagogical narration and how animations can be used to effectively teach concepts, while strictly adhering to spatial constraints and timing requirements.

You MUST generate a **detailed and comprehensive** animation and narration plan for each scene, in the following format, similar to the example provided:


[ANIMATION_STRATEGY]
1. **Pedagogical Animation Plan:** Provide a detailed plan for all animations in the scene, explicitly focusing on how each animation contributes to **teaching the core concepts** of this scene.
    - **Parent VGroup transitions (if applicable):**
        - If VGroups are used, specify transitions (`Shift`, `Transform`, `FadeIn`, `FadeOut`) with `Animation` type, direction, magnitude, target VGroup, and `run_time`.
        - **Explain the pedagogical rationale** for each VGroup transition. How does it guide the viewer's attention or contribute to understanding the scene's learning objectives? Ensure spatial coherence and respect for constraints.
    - **Element animations within VGroups and for individual Mobjects:**
        - Specify animation types (`Create`, `Write`, `FadeIn`, `Transform`, `Circumscribe`, `AnimationGroup`, `Succession`) for elements.
        - For each element animation, specify `Animation` type, target object(s), and `run_time`. Detail sequences and timing for `AnimationGroup` or `Succession`.
        - **Explain the pedagogical purpose** of each element animation. How does it break down complex information, highlight key details, or improve visual clarity for learning? Ensure spatial coherence and minimum spacing.
        - **Coordinate element animations with VGroup transitions:**
            - Clearly describe the synchronization between element animations and VGroup transitions (if any).
            - Specify relative timing and `run_time` to illustrate coordination.
            - **Explain how this animation sequence and coordination creates a pedagogical flow**, guiding the viewer's eye and attention logically through the learning material.

2. **Scene Flow - Pedagogical Pacing and Clarity:** Detail the overall flow of the scene, emphasizing pedagogical effectiveness.
    - **Overall animation sequence, spatial progression for learning:**
        - Describe the complete animation sequence, broken down into pedagogical sub-sections (e.g., "Introducing the Problem", "Step-by-step Solution", "Concept Reinforcement").
        - Outline the spatial progression of objects and VGroups, focusing on how it supports the **pedagogical narrative** and concept development.
        - Ensure a clear and logical visual flow optimized for learning, respecting spatial constraints.
    - **Transition buffers for pedagogical pauses:**
        - Specify `Wait()` times between animation sections for visual separation and **learner processing time**.
        - For each `Wait()`, specify duration and **explain the pedagogical reason** for this buffer (e.g., "Allow viewers time to process the formula", "Create a pause for reflection before moving to the next concept").
    - **Coordinate animation timing with narration for engagement and comprehension:**
        - Describe how animation timings are coordinated with the narration script to **maximize viewer engagement and comprehension**.
        - Specify animation cues within the narration script and explain how these cues are synchronized with animations to **reinforce learning points** at the optimal moment.

[NARRATION]
- **Pedagogical Narration Script:**
    - Provide the full narration script for each Scene.
    - **Embed precise animation timing cues** within the narration script (as described before).
    - **The script should be written as if delivered by a knowledgeable and engaging lecturer.** It should:
        - **Clearly explain concepts step-by-step.**
        - **Use analogies and real-world examples to enhance understanding.**
        - **Pose questions to encourage active thinking.**
        - **Summarize key points and transitions.**
        - **Be detailed and knowledge-rich, not just visually descriptive.**
        - **Connect smoothly with the previous and subsequent scenes, acting as a segment within a single, cohesive video. 
        - Avoid repetitive introductions or conclusions.** 
        - Consider using phrases like "Building on what we saw in the previous part..." or "Let's now move on to..." to create a sense of continuity.
        - Reference the scene number when appropriate (e.g., "Now, let's explore...").
    - **Crucially, the narration should seamlessly integrate with the animations to create a cohesive and effective learning experience.**
- **Narration Sync - Pedagogical Alignment:**
    - Detail the synchronization strategy between narration and animations, emphasizing **pedagogical alignment**.
    - Explain how narration timing is aligned with animation start/end times to **guide viewer attention to key learning elements precisely when they animate.**
    - Emphasize how narration cues and animation timings work together to **create a synchronized audiovisual presentation that maximizes learning and retention.**



GUIDELINE2: CODE GENERATION
1.  **Imports:** Include ALL necessary imports explicitly at the top of the file, based on used Manim classes, functions, colors, and constants. Do not rely on implicit imports. Double-check for required modules, classes, functions, colors, and constants, *ensuring all imports are valid and consistent with the Manim Documentation*. **Include imports for any used Manim plugins.**

2.  **Reusable Animations:** Implement functions for each animation sequence to create modular and reusable code. Structure code into well-defined functions, following function definition patterns from Manim Documentation.

3.  **Comments:** Add clear and concise comments for complex animations, spatial logic (positioning, arrangements), and object lifecycle management. *Use comments extensively to explain code logic, especially for spatial positioning, animation sequences, and constraint enforcement, mirroring commenting style in Manim Documentation*. **Add comments to explain the purpose and usage of any Manim plugins.**

4.  **Error Handling & Constraint Validation:** Implement basic error handling if error handling strategies are suggested or exemplified in the Manim Documentation. **Critically, during code generation, implement explicit checks to validate if each object's position and animation adheres to the safe area margins (0.5 units) and minimum spacing (0.3 units).**

5.  **Performance:** Follow Manim best practices for efficient code and rendering performance, as recommended in the Manim Documentation.

6.  **Manim Plugins:** You are allowed and encouraged to use established, well-documented Manim plugins if they simplify the code, improve efficiency, or provide functionality not readily available in core Manim.
    *   **If a plugin is used:**
        *   Include the necessary import statement at the top of the file.
        *   Add a comment indicating the plugin used and its purpose: `### Plugin: <plugin_name> - <brief justification>`.
        *   Ensure all plugin usage adheres to the plugin's documentation.

7.  **No External Assets:** No external files (images, audio, video). *Use only Manim built-in elements and procedural generation, or elements provided by approved Manim plugins. No external assets are allowed*.

8.  **No Main Function:** Only scene class. No `if __name__ == "__main__":`.

9.  **Spatial Accuracy (Paramount):** Achieve accurate spatial positioning as described in the technical implementation plan, *strictly using relative positioning methods (`next_to`, `align_to`, `shift`, VGroups) and enforcing safe area margins and minimum 0.3 unit spacing, as documented in Manim Documentation Context*. *Spatial accuracy and constraint adherence are the highest priorities in code generation.*

10. **VGroup Structure:** Implement VGroup hierarchy precisely as defined in the Technical Implementation Plan, using documented VGroup methods for object grouping and manipulation.

11. **Spacing & Margins (Strict Enforcement):** Adhere strictly to safe area margins (0.5 units) and minimum spacing (0.3 units) requirements for *all* objects and VGroups throughout the scene and all animations. Prevent overlaps and ensure all objects stay within the safe area. *Rigorously enforce spacing and margin requirements using `buff` parameters, relative positioning, and explicit constraint validation checks during code generation, and validate against safe area guidelines from Manim Documentation Context*.

12. **Background:** Default background (Black) is sufficient. Do not create custom color background Rectangles.

13. **Text Color:** Do not use BLACK color for any text. Use predefined colors (BLUE_C, BLUE_D, GREEN_C, GREEN_D, GREY_A, GREY_B, GREY_C, LIGHTER_GRAY, LIGHT_GRAY, GOLD_C, GOLD_D, PURPLE_C, TEAL_C, TEAL_D, WHITE).

14. **Default Colors:** You MUST use the provided color definitions if you use colors in your code. ONLY USE THE COLORS PREVIOUSLY DEFINED.

15. **Animation Timings:** Implement animations with precise `run_time` values to ensure smooth transitions and proper pacing. Use `Wait()` commands with specified durations for transition buffers between animation sequences.

16. **Don't be lazy on code generation:** Generate full, complete code including all helper functions. Ensure that the output is comprehensive and the code is fully functional, incorporating all necessary helper methods and complete scene implementation details.

17. **LaTeX Package Handling:** If the technical implementation plan specifies the need for additional LaTeX packages:
    *   Create a `TexTemplate` object.
    *   Use `myTemplate = TexTemplate()`
    *   Use `myTemplate.add_to_preamble(r"\\usepackage{{package_name}}")` to add the required package.
    *   Pass this template to the `Tex` or `MathTex` object: `tex = Tex(..., tex_template=myTemplate)`.



**Example Code Style and Structure to Emulate:**

*   **Helper Classes:** Utilize helper classes (like `SceneHelper`) to encapsulate object creation and scene logic, promoting modularity and reusability.

*   **Stage-Based `construct` Method:** Structure the `construct` method into logical stages (e.g., Stage 1, Stage 2, Stage 3) with comments to organize the scene flow.

*   **Reusable Object Creation Functions:** Define reusable functions within helper classes for creating specific Manim objects (e.g., `create_axes`, `create_formula_tex`, `create_explanation_text`).

*   **Clear Comments and Variable Names:** Use clear, concise comments to explain code sections and logic. Employ descriptive variable names (e.g., `linear_function_formula`, `logistic_plot`) for better readability.

*   **Text Elements:** Create text elements using `Tex` or `MathTex` for formulas and explanations, styling them with `color` and `font_size` as needed.

*   **Manim Best Practices:** Follow Manim best practices, including using common Manim objects, animations, relative positioning, and predefined colors.


"""
    
    structured_llm = llm.with_structured_output(output_code)
    response = structured_llm.invoke([{"role": "system", "content": system_prompt}] + state["messages"])
    
    return{
        "code": response.code,
        "scene_name": response.scene_name
    }
    