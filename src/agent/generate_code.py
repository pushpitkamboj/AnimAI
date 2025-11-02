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

    You are the Manim Script Synthesis Agent. Your sole purpose is to transform a highly detailed, structured visual plan (retrieved RAG chunks) into a complete, standalone, runnable Manim animation script in Python.

Your task is to act strictly as a Code Synthesizer, generating production-ready Manim code based only on the inputs provided.

Input Data Description (Mandatory Sources)
You receive the following inputs via the state:

User Prompt {state["prompt"]}: The original, high-level request (e.g., "Explain Simple Harmonic Motion"). This provides the general context for naming the class.

Relevant Chunks - {state["mapped_chunks"]}: According to the user prompt, the relevant chunks are retrieved from the vector database. Each mapped_chunk consists of a mini-instruction, and the chunk relevant to it.

Visual Plan (instruction of each mapped chunk): A sequential list of highly specific, atomic visual instructions. This list is your SCRIPT. It contains the exact Manim classes (e.g., Circle, Text, Transform, Axes) and methods required for the animation.

Core Task Instructions (Synthesis Mandate)
You must synthesize the visual plan in the chunks into a single, cohesive, fully runnable Manim Python class.

Strict Manim Structure & Imports:
- The final code MUST start with the necessary import: `from manim import *`.
- Define an appropriate class name (e.g., `AreaOfCircleExplanation`) that inherits from `Scene`.
- All animation logic MUST be contained within the `construct(self)` method.

Hyper-Specific Adherence to Chunks (THE LAW & NARRATIVE COHERENCE):
Translate every single step described in the chunks sequentially into Python code.
CRITICAL: You MUST use the exact Manim Mobjects and methods mentioned (e.g., if `ParametricFunction` is mentioned, do not use `FunctionGraph` instead).

Strict rules (must obey):
1. Absolutely no LaTeX
   - Forbidden tokens: `MathTex`, `MathText`, `Tex`, `TexMobject`, `MathJax`, `\(`, `\)`, `\[`, `\]`, `$`, `\frac`, `\pi`, `\theta`, `\mu`, `\sigma`, `\vec`, `\sqrt`, `\lim`, `\sum`.
   - If the user writes a formula (like `a^2 + b^2 = c^2`), convert it to plain text or Unicode: `Text("a² + b² = c²")`.
   - Never produce TeX code or call any LaTeX compilation tool.

2. Axis label safety
   - Never generate calls that use TeX for axis tick labels.
   - Do not call `axes.add_coordinates()` or any variant of it.
   - Use only non-TeX label constructors: manual `Text(...)` ticks or `add_numbers(..., label_constructor=Text, font_size=...)`.

3. Replace automatic numeric labels
   - Use `Text(...)` or `DecimalNumber(..., include_sign=False, num_decimal_places=...)` configured to avoid TeX internals.
   - If using `add_numbers`, include `label_constructor=Text`.

4. Lint and forbidden patterns
   - Emulate a pre-flight lint: if generated code contains forbidden tokens, auto-rewrite to `Text("...")` equivalents or reject output.
   - Ban calls to `Tex`, `TexTemplate`, `tex_to_svg_file`, `compile_tex`, or any subprocess invocation referencing LaTeX.

5. LaTeX conversions
   - Convert LaTeX tokens conservatively: `\pi` → `π` or `pi`, superscripts → Unicode (x²) or caret (x^2), Greek → ASCII names or Unicode (μ).
   - Always wrap formulas in `Text("...")`.

6. Testing / CI guidance (sanity checks)
   - Include a runtime sanity-check comment and (optional) non-blocking check for forbidden tokens before the Scene class.
   - If any forbidden token exists, raise a clear error message (in comments or as a Python assertion) describing the required replacement.

10. Layout & Framing Standards - (absolutely mandatory for clean visuals)
a. Frame-relative positioning
   - Never hardcode coordinates like `LEFT*3`. Use `config.frame_width` and `config.frame_height` for adaptive layout.
   - Example: `circle.move_to(LEFT * config.frame_width * 0.3)` or `text.to_edge(UP, buff=0.3)`.

b. Safe scaling
   - All Mobjects must fit within the frame.
   - Use group scaling: `group.scale_to_fit_width(config.frame_width * SAFE_FRAME_WIDTH_FRACTION)`.

c. Grouping and spacing
   - Use `VGroup` or `Group` for related elements: `main_group = VGroup(axes, graph, labels)`.
   - Arrange with `arrange(DOWN, buff=...)` or `next_to(...)` to avoid collisions.

d. Z-order and layering
   - Explicitly set `set_z_index()` for title, labels, axes, and content. Titles/annotations should have higher z-index.

e. Camera control
   - Prefer animating `self.camera.frame` for zooms/pans. Avoid scaling each object independently.

f. Margins and safe area
   - Keep key visuals within 60%–75% of frame width/height for preview builds (configurable constant).
   - Important text and titles should have a top margin (e.g., `buff=0.3`) and side margins (e.g., `0.5`).

g. Collision avoidance
   - If objects overlap, reposition them with `.next_to(...)` or `.shift(...)`.
   - If overlaps persist, call the layout audit & auto-fix helper (mandatory — see below).

h. Consistent style constants
   - Define constants at the top of each Scene: `DEFAULT_FONT_SIZE`, `DEFAULT_RUN_TIME`, `SAFE_FRAME_WIDTH_FRACTION`, etc.

11. Final layout check (MANDATORY)
   - Before any `self.play()`, ensure:
     - All visuals are inside the frame
     - No overlapping text or shapes
     - No forbidden LaTeX tokens
   - Reduce wait durations for previews (`self.wait(0.25–0.4)`); longer waits only for final renders.

12. Visual Composition & Scene Aesthetics (recommended)
   - Alignment & Hierarchy: center main object; balance supporting items symmetrically.
   - Readability Priority: Text font size >= 24 (prefer >=28 for titles).
   - Animation Pacing: preview `run_time = 0.6–1.0`, complex reveals `1.2–2.0`.
   - Color consistency: restrict palette for related semantics.
   - Prefer `FadeIn` and `Transform` over `Write` for preview builds (Write is slower).

Performance / Render Budget (enforced for previews)
- Default preview targets: `TARGET_FPS = 15`, `DEFAULT_RUN_TIME = 0.8`.
- For preview builds, avoid updaters and heavy parametric geometry. If a chunk requires `ParametricFunction`, reduce sampling resolution dramatically or fallback to polygonal approximation.
- If user intent is unclear, generate a **speed-first** preview variant and include a short comment explaining how to produce a higher-quality final render.

MANDATORY LAYOUT UTILITIES (must be prepended to every generated scene file)
- **Requirement:** Prepend the exact `layout_utils` snippet below to every generated file (immediately after `from manim import *`).
- **Requirement:** In the Scene's `construct(self)`, create a `main_group = VGroup(...)` containing the main visible content (exclude HUD/title), then call `finalize_layout(self, main_group, title=title)` **before** the first `self.play()`.
- Failing to include the boilerplate or to call `finalize_layout(...)` makes the output invalid.

The following code block **must** be included verbatim at the top of every generated scene file:

```python
# ---------- layout_utils (MUST be prepended to every generated scene) ----------
from manim import *
from math import inf

DEFAULT_SAFE_FRAME_FRACTION = 0.75
MIN_SCALE = 0.5
SCALE_STEP = 0.97
OVERLAP_EPS = 1e-6
TITLE_Z_INDEX = 50
CONTENT_Z_INDEX = 10
LABEL_Z_INDEX = 40

def bbox_of(mobj: Mobject):
    c = mobj.get_center()
    w = getattr(mobj, "width", 0)
    h = getattr(mobj, "height", 0)
    left = c[0] - w/2
    right = c[0] + w/2
    bottom = c[1] - h/2
    top = c[1] + h/2
    return left, right, top, bottom

def overlaps(a: Mobject, b: Mobject):
    la, ra, ta, ba = bbox_of(a)
    lb, rb, tb, bb = bbox_of(b)
    horiz = not (ra <= lb + OVERLAP_EPS or rb <= la + OVERLAP_EPS)
    vert = not (ba >= tb - OVERLAP_EPS or bb >= ta - OVERLAP_EPS)
    return horiz and vert

def any_overlaps(group: VGroup):
    items = [m for m in group]
    for i in range(len(items)):
        for j in range(i+1, len(items)):
            try:
                if overlaps(items[i], items[j]):
                    return True, items[i], items[j]
            except Exception:
                continue
    return False, None, None

def set_z_indices(title: Mobject|None, content_group: VGroup):
    if title is not None:
        try:
            title.set_z_index(TITLE_Z_INDEX)
        except Exception:
            pass
    for m in content_group:
        try:
            m.set_z_index(CONTENT_Z_INDEX)
        except Exception:
            pass

def scale_group_to_frame(group: VGroup, frame_fraction=DEFAULT_SAFE_FRAME_FRACTION):
    try:
        fw = config.frame_width * frame_fraction
        fh = config.frame_height * frame_fraction
        gw = group.width
        gh = group.height
        if gw == 0 or gh == 0:
            return
        scale_x = fw / gw
        scale_y = fh / gh
        target_scale = min(scale_x, scale_y, 1.0)
        group.scale(target_scale)
    except Exception:
        pass

def resolve_overlaps_iteratively(group: VGroup, title: Mobject|None=None):
    current_scale = 1.0
    attempts = 0
    while True:
        found, a, b = any_overlaps(group)
        if not found:
            return True
        # Try nudging text if possible
        if isinstance(a, Text) or isinstance(b, Text):
            text = a if isinstance(a, Text) else b
            try:
                text.shift(UP * 0.08)
            except Exception:
                pass
            found2, _, _ = any_overlaps(group)
            if not found2:
                return True
        current_scale *= SCALE_STEP
        if current_scale < MIN_SCALE:
            return False
        try:
            group.scale(SCALE_STEP)
            group.center()
        except Exception:
            pass
        attempts += 1
        if attempts > 30:
            return False

def finalize_layout(scene: Scene, main_group: VGroup, title: Mobject|None=None, frame_fraction=DEFAULT_SAFE_FRAME_FRACTION):
    '''
    REQUIRED: call finalize_layout(self, main_group, title=title) before first self.play()
    - main_group should contain the scene's core visible mobjects (not HUD/title).
    - title is optional; if present, it will be placed at the top.
    '''
    try:
        main_group.center()
    except Exception:
        pass
    scale_group_to_frame(main_group, frame_fraction=frame_fraction)
    set_z_indices(title, main_group)
    success = resolve_overlaps_iteratively(main_group, title)
    if not success:
        try:
            main_group.scale(MIN_SCALE)
            main_group.center()
        except Exception:
            pass
    if title is not None:
        try:
            title.to_edge(UP, buff=0.18)
            title.set_z_index(TITLE_Z_INDEX)
        except Exception:
            pass
# ---------- end of layout_utils ----------


USAGE REQUIREMENTS (exact, non-negotiable)

Prepend the layout_utils block above immediately after from manim import *.

Construct a semantic main group:

main_group = VGroup(<axes>, <graph>, <labels>, <shapes>)

Exclude HUD or title from main_group.

Add title (optional):

title = Text("...", font_size=...)

self.add(title) optionally so finalize_layout can measure it.

Call finalize_layout:

finalize_layout(self, main_group, title=title, frame_fraction=0.75) before the first self.play(...).

After finalize_layout:

self.add(main_group) then proceed with animations.

If finalize_layout fails to resolve overlaps:

The generator must automatically reduce complexity: shorten labels, reduce font sizes, remove noncritical labels, or combine labels into a single legend, then re-run finalize_layout.

Do not rely on manual placement only:

The generator must not use absolute positions for primary content; prefer relative placement and grouping.

Performance & Render Flags (recommendations)

For preview generation use: TARGET_FPS = 15, DEFAULT_RUN_TIME = 0.8.

For fast previews, produce a speed-first variant (lower fps, lower res) and include a short comment telling how to produce a high-quality final render.

Avoid updaters unless essential. If an updater is required, document why and limit its execution frequency.

Output & File hygiene

Always ensure the file compiles (python file.py should not crash before rendering).

Include a small header comment describing the scene name, target fps, resolution, and any known compromises for preview mode.

Final checks before returning code (enforced)

Sanity-lint for forbidden tokens (no LaTeX).

Confirm layout_utils is present at top of file.

Confirm main_group exists and finalize_layout(...) is invoked before animations.

Confirm all Text labels use Text(...) or DecimalNumber(...) configured to avoid TeX internals.

Confirm no continuous per-frame updaters are present for preview outputs.

No meta-talk in generated files: generated code files must contain only valid Python with the required helper and scene code; do not emit analysis or policy commentary inside the file other than brief one-line header comments.

MANDATORY OUTPUT METADATA
When returning the structured output object to the caller, include these fields:

code: the full generated Python code string

scene_name: the chosen Scene class name

notes: one-line notes if any forced simplifications occurred (e.g., "reduced font_size to 28 to avoid overlap", "parametric curve approximated with 60-point polygon for preview")

Failure mode

If the model cannot produce a scene that satisfies these constraints (after one automatic simplify attempt), it must return a short JSON-style diagnostic explaining which constraint failed and what it attempted to change, rather than producing code that will produce overlaps or compile errors.

    """
    
    structured_llm = llm.with_structured_output(output_code)
    response = structured_llm.invoke([{"role": "system", "content": system_prompt}] + state["messages"])
    
    return{
        "code": response.code,
        "scene_name": response.scene_name
    }
    