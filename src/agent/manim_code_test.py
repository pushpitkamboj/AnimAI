from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService
import math

class CubicEquationScene(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService(lang="en", tld="com"))  # Use GTTS for voiceover

        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-10, 10, 2],
            axis_config={"include_tip": False},
        )
        graph = axes.plot(lambda x: x**3 - 3*x, color=BLUE)

        sqrt3 = math.sqrt(3)
        root1 = Dot(axes.c2p(-sqrt3, 0), color=RED)
        root2 = Dot(axes.c2p(0, 0), color=RED)
        root3 = Dot(axes.c2p(sqrt3, 0), color=RED)

        label1 = MathTex(r"(-\sqrt{3},\ 0)").scale(0.7).next_to(root1, DOWN)
        label2 = MathTex(r"(0,\ 0)").scale(0.7).next_to(root2, DOWN)
        label3 = MathTex(r"(\sqrt{3},\ 0)").scale(0.7).next_to(root3, DOWN)

        intro_text = Tex("Let's explore a cubic equation!").scale(1.2)
        self.play(Write(intro_text))
        self.wait(2)
        self.play(FadeOut(intro_text))

        with self.voiceover(text="This is the graph of the cubic equation x cubed minus three x.") as tracker:
            self.play(Create(axes), run_time=tracker.duration)

        with self.voiceover(text="You can see it has a distinctive S shape.") as tracker:
            self.play(Create(graph), run_time=tracker.duration)
            self.wait(1)

        with self.voiceover(text="The points where the graph crosses the x-axis are called the roots or solutions of the equation.") as tracker:
            self.play(Create(root1), Create(root2), Create(root3), run_time=tracker.duration)
        self.play(Write(label1), Write(label2), Write(label3))
        self.wait(2)

        with self.voiceover(text="These roots are important because they represent the values of x that make the equation equal to zero.") as tracker:
            self.play(FadeOut(label1), FadeOut(label2), FadeOut(label3), run_time=tracker.duration)
            self.wait(2)

        conclusion_text = Tex("That's a brief look at cubic equations!").scale(1.2)
        self.play(FadeOut(root1), FadeOut(root2), FadeOut(root3))
        self.play(FadeOut(graph), FadeOut(axes))
        self.play(Write(conclusion_text))
        self.wait(2)
        self.play(FadeOut(conclusion_text))
        self.wait(1)
