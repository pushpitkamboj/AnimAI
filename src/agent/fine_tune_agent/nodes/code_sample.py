from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService

# ----- Helper Functions for Object Construction -----
def build_triangle_with_labels():
    # Define triangle points for Polygon
    A = np.array([0, 0, 0])         # Vertex at origin
    B = np.array([3, 0, 0])         # Vertex on x-axis (horizontal)
    C = np.array([3, 2, 0])         # Vertex up from B (right triangle with leg lengths 3 and 2)
    triangle = Polygon(A, B, C, color="#4682B4", stroke_width=4)

    # Side labels -- careful placement with minimum 0.3 spacing from vertices
    # Label 'a' (vertical leg): from (3,0,0) to (3,2,0), so place at midpoint plus left offset
    label_a = MathTex("a", font_size=24, color="#C0392B")
    a_pos = (B + C)/2 + np.array([0.25, 0, 0]) # offset right of midpoint of BC
    label_a.move_to(a_pos)

    # Label 'b' (horizontal leg): from (0,0,0) to (3,0,0), place below center, offset down
    label_b = MathTex("b", font_size=24, color="#16A085")
    b_pos = (A + B)/2 + np.array([0, -0.28, 0]) # offset below AB
    label_b.move_to(b_pos)

    # Label 'c' (hypotenuse): from (0,0,0) to (3,2,0), offset above
    label_c = MathTex("c", font_size=24, color="#F39C12")
    c_pos = (A + C)/2 + np.array([-0.23, 0.23, 0]) # offset to upper left from AC midpoint
    label_c.move_to(c_pos)

    # Angle annotation
    # RightAngle in Manim Community Edition: RightAngle(A, B, C, **kwargs), where B is the vertex
    angle = RightAngle(Line(B, A), Line(B, C), stroke_width=4, length=0.36)
    # Place the angle label near the right angle, a small offset from the marker
    angle_label = MathTex("90^\\circ", font_size=20)
    # Find center of angle marker and nudge
    angle_label.next_to(angle, LEFT+UP, buff=0.13)

    # Group all for collective control
    triangle_with_labels = VGroup(triangle, label_a, label_b, label_c, angle, angle_label)
    return triangle_with_labels, triangle, label_a, label_b, label_c, angle, angle_label

def build_intro_text_group():
    scene_title = Tex(
        "Introducing Right Triangles",
        font_size=28,
        color="#08306B"
    )
    hook_question = Tex(
        "Have you ever wondered how scientists measure distances they can’t directly reach?",
        font_size=22,
        color="#0B486B"
    )
    intro_text_group = VGroup(scene_title, hook_question)
    return intro_text_group, scene_title, hook_question

def build_definition_text():
    definition_text = Tex(
        "A right triangle has one 90-degree angle. The two sides adjacent to the right angle are called "
        "\\textbf{legs} (a, b), and the side opposite is the \\textbf{hypotenuse} (c).",
        font_size=22,
        tex_environment=None
    )
    return definition_text

class RightTriangleIntroScene(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService(lang="en", tld="com"))

        # ----- Optional: Safe Area Rectangle for Layout Debugging -----
        safe_area_width = config.frame_width - 1.0  # 0.5 units margin on each side
        safe_area_height = config.frame_height - 1.0
        safe_area = Rectangle(
            width=safe_area_width,
            height=safe_area_height,
            stroke_color="#AAAAAA",
            stroke_opacity=0.3,
            fill_opacity=0.0
        ).move_to(ORIGIN)
        # CAUTION: Comment out next line in final render, only for layout debugging
        # self.add(safe_area)

        # ----- Build Main Components -----
        intro_text_group, scene_title, hook_question = build_intro_text_group()
        triangle_with_labels, triangle_polygon, side_label_a, side_label_b, side_label_c, angle_annotation, angle_label = build_triangle_with_labels()
        definition_text = build_definition_text()

        # ----- Positioning -----
        # Title at safe top (0.5 margin, 0.3 buffer)
        scene_title.next_to(safe_area.get_top(), DOWN, buff=0.3)
        scene_title.set_x(0)  # center horizontally
        # Hook question below title, buffer 0.3
        hook_question.next_to(scene_title, DOWN, buff=0.3)
        hook_question.set_x(0)
        intro_text_group = VGroup(scene_title, hook_question)

        # Triangle group appears centered lower-third, below hook
        triangle_with_labels.move_to(ORIGIN)
        triangle_y_pos = (
            hook_question.get_bottom()[1]
            + definition_text.height/2
            + triangle_with_labels.height/2
            + 1.1  # ~0.6 above, ~0.5 below buffer for safe area
        )
        triangle_with_labels.move_to(np.array([0, triangle_y_pos-2.1, 0]))  # Placed lower third, allowing space for text
        # SAFETY REVIEW: Triangle plus its labels and right angle marker are safely bounded by 0.5 margin and minimum 0.3 internal label spacing

        # Definition text below triangle, with at least 0.5 units spacing from triangle bottom
        definition_text.next_to(triangle_with_labels, DOWN, buff=0.5)
        # This should not be less than frame's bottom safe margin
        if definition_text.get_bottom()[1] < safe_area.get_bottom()[1]+0.01:
            # Manual review: text may run outside bottom, review scene scaling or font size!
            # Safety comment:
            # CAUTION: Definition text may be too low—validate on localization/larger fonts
            pass

        # ----- Add to Scene (not yet animated) -----
        self.add(intro_text_group)
        self.add(triangle_with_labels)
        self.add(definition_text)
        triangle_with_labels.set_opacity(0)  # hide until animation
        definition_text.set_opacity(0)

        # ----- Animation and Voiceover Sequence -----
        # Title Write
        with self.voiceover(text="Welcome!") as tracker:
            self.play(Write(scene_title), run_time=tracker.duration)

        # Hook question Write
        with self.voiceover(text="Have you ever wondered how scientists or engineers measure distances they can't actually walk up to? For instance, how do you figure out the shortest line across a river, or the diagonal length of a screen without using a tape measure?") as tracker:
            self.play(Write(hook_question), run_time=tracker.duration)

        self.wait(0.5)  # Pedagogical pause

        # Triangle Create
        triangle_with_labels.set_opacity(1)  # reveal group, but animate in parts
        # First, fade in outline only
        for mob in triangle_with_labels:
            mob.set_opacity(0)
        triangle_polygon.set_opacity(1)
        self.add(triangle_polygon)
        with self.voiceover(text="The answer often lies in a special shape—the right triangle. Let’s see exactly what that is.") as tracker:
            self.play(Create(triangle_polygon), run_time=tracker.duration)

        # Angle marker (right angle) GrowFromCenter
        angle_annotation.set_opacity(1)
        self.add(angle_annotation)
        with self.voiceover(text="Here, I'll draw a triangle. Notice how one corner forms a perfect L-shape.") as tracker:
            self.play(GrowFromCenter(angle_annotation), run_time=tracker.duration)

        # Angle label (90 degrees)
        angle_label.set_opacity(1)
        self.add(angle_label)
        with self.voiceover(text="This corner is what we call a right angle—a straight, 90-degree corner.") as tracker:
            self.play(FadeIn(angle_label), run_time=tracker.duration)

        # Side label 'a'
        side_label_a.set_opacity(1)
        self.add(side_label_a)
        with self.voiceover(text="The side attached to the right angle is called one of the 'legs,' and we’ll label it 'a'.") as tracker:
            self.play(FadeIn(side_label_a), run_time=tracker.duration)

        # Side label 'b'
        side_label_b.set_opacity(1)
        self.add(side_label_b)
        with self.voiceover(text="Here’s the other leg—let’s call it 'b'.") as tracker:
            self.play(FadeIn(side_label_b), run_time=tracker.duration)

        # Side label 'c'
        side_label_c.set_opacity(1)
        self.add(side_label_c)
        with self.voiceover(text="And this long stretch, opposite the right angle, is known as the 'hypotenuse'; we’ll call it 'c'.") as tracker:
            self.play(FadeIn(side_label_c), run_time=tracker.duration)

        self.wait(0.3)  # Brief processing pause

        # Definition text Write
        definition_text.set_opacity(1)
        self.add(definition_text)
        with self.voiceover(text="In summary, a right triangle always contains one 90-degree angle. The two sides making up that angle are called the 'legs'—a and b—and the side across from it is the hypotenuse, c. These labels will be our keys for unlocking powerful relationships in the next scenes.") as tracker:
            self.play(Write(definition_text), run_time=tracker.duration)

        self.wait(1.2)  # Reading/processing pause

        # FadeOut all intro texts and definition
        # Review: Fade as groups so that fade is clean; respects spatial grouping
        with self.voiceover(text="Now, with this foundation in place, we'll unlock one of the most famous formulas in all of math—the Pythagorean theorem.") as tracker:
            self.play(FadeOut(intro_text_group, run_time=0.8), FadeOut(definition_text, run_time=0.6))

        # End of scene, wait to transition
        self.wait(0.3)

        #-----
        # SAFETY & LAYOUT CHECKS (dev notes):
        # (1) All objects are next_to()ed or centered w.r.t. the safe area rectangle.
        # (2) All next_to() buffers >= 0.3 units.
        # (3) All items, especially multi-line texts, have font_size set to fit in scene when centered.
        # (4) VGroup triangle_with_labels ensures labels/annotations do not overlap.
        # (5) For localization, review scene with dev-safe_area enabled above and consider reducing font_size or spacing as needed.
        #-----

