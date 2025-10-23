from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from pydantic import BaseModel
from typing import List

from agent.graph_state import State
llm = init_chat_model("openai:gpt-4.1")

class output_format(BaseModel):
    steps: List[str]
    

def enhanced_prompt(state: State):
    prompt = """        
        You are an expert script writer of animated videos. You have to break down the user prompt into enhanced prompt.
        decompose the user's request into atomic, Manim-specific actions to effectively query your specialized vector database. Each sub-query should be a standalone, retrievable command or concept.
        make the enhanced prompt exceptionally descriptive and effective for a RAG system searching Manim commands

        egs -
        eg1 . user - explain projectile motion
        "enhanced prompt = [Use the **Axes class** with appropriate tick marks and labels for $x$ and $y$ to draw a fully labeled 1st quadrant coordinate system, setting the **NumberPlane** as the background grid"
        "Use the **Dot or Sphere class** to create the projectile Mobject (the ball), initially placed at the **ORIGIN**"
        "Draw the initial velocity using the **Vector class** and label it *$\vec{v}_0$* with the **MathTex class**; draw the launch angle $\theta$ using the **Angle class** with the positive x-axis"
        "Apply the **Transform animation** to break the initial velocity vector $\vec{v}0$ into its two components: a horizontal component $\vec{v}{0x}$ and a vertical component $\vec{v}_{0y}$"
        "Use **MathTex** to explicitly state the initial velocity components: *$\vec{v}_{0x} = v_0 \cos\theta$* and *$\vec{v}_{0y} = v_0 \sin\theta$*"
        "Define the theoretical path using the **ParametricFunction class** based on the projectile equation: $y(t) = (v_0 \sin\theta)t - \frac{1}{2}gt^2$ and $x(t) = (v_0 \cos\theta)t$"
        "Use the **MoveAlongPath animation** for the ball Mobject, making it follow the precisely defined **parabolic FunctionGraph**"
        "Use an **always_redraw updater** to continuously draw a *horizontal velocity vector* ($\vec{v}_x$) that remains constant in magnitude throughout the flight"
        "Use a second **always_redraw updater** to draw a *vertical velocity vector* ($\vec{v}_y$) that continuously decreases, becomes zero at the peak, and increases downward"
        "Use the **Arrow class** to constantly draw the downward *acceleration vector $\vec{g}$* at the projectile's position, labeled $9.8 \text{ m/s}^2$"
        "At the peak of the trajectory, use **Succession** to **Pause** the animation, zoom in, and use **FadeTransform** to show that $\vec{v}_y = 0$ while $\vec{v}_x$ is maximum"

        ]

        eg2. user - explain  the pythagoras theorem 
        "enhanced prompt = [Use the **Polygon class** or **Triangle class** to draw a clearly visible *right-angled triangle*, ensuring the right angle is clearly marked with a **Square Mobject** or an arc"
        "Use the **Text class** or **MathTex class** to precisely label each *vertex* of the triangle as *A, B, and C* (with C being the right angle)"
        "Use the **Line class** to represent each side, and then use **MathTex** to label the lengths of the sides opposite the vertices as *$a$* (vertical leg), *$b$* (horizontal leg), and *$c$* (hypotenuse)"
        "Construct a large, distinct **Square Mobject** on the outer side of leg $a$, explicitly using **Square.set_fill** with a specific color (e.g., BLUE) and **MathTex** to label its area as *$a^2$*"
        "Construct a large, distinct **Square Mobject** on the outer side of leg $b$, explicitly using **Square.set_fill** with a different color (e.g., RED) and **MathTex** to label its area as *$b^2$*"
        "Construct a large, distinct **Square Mobject** on the outer side of the hypotenuse $c$, explicitly using **Square.set_fill** with a third color (e.g., GREEN) and **MathTex** to label its area as *$c^2$*"
        "Animate a **FadeOut** of the original triangle, leaving only the three squares"
        "Perform a **Transform animation** or a sequence of **Rotate and Translate animations** on the **Square Mobject $a^2$** and the **Square Mobject $b^2$"
        "The goal of the animation is to show the pieces of *$a^2$ and $b^2$ being cut and rearranged* (e.g., using **Difference or Intersection Mobjects** to simulate cuts) to *perfectly fill the area* of the **Square Mobject $c^2$"
        "Highlight the moment of perfect fit with a **Flash animation** or a color pulse on $c^2$"
        "Display the final *Pythagorean theorem equation* prominently in the center of the screen using large, bold **MathTex*: **$a^2 + b^2 = c^2$*"
        ]

        eg3. user - Show the derivative of x^2
        "enhanced prompt = [Use the **Axes class** with labeled x and y axes (e.g., $x$ and $f(x)$) to draw a standard Cartesian plane, possibly using a **NumberPlane** grid for context"
        "Plot the function *$f(x) = x^2$* using the **FunctionGraph class**, setting a distinct color (e.g., YELLOW)"
        "Use the **Dot class** to place a *point Mobject P* at a general point on the curve, $(x, x^2)$"
        "Use the **Dot class** to place a second *point Mobject Q* at a nearby location on the curve, $(x + \Delta x, (x + \Delta x)^2)$"
        "Use the **DashedLine class** to draw the horizontal distance *$\Delta x$* and the vertical distance *$\Delta f$* between P and Q"
        "Draw the **Line class Mobject** representing the *secant line* passing through points P and Q"
        "Use the **MathTex class** to display the formula for the slope of the secant line: *$m_{\text{sec}} = \frac{\Delta y}{\Delta x} = \frac{(x+\Delta x)^2 - x^2}{\Delta x}$*"
        "Animate **point Q using the MoveAlongPath method** to smoothly approach and nearly coincide with point P, illustrating the limit process where *$\Delta x \to 0$*"
        "Simultaneously, apply the **Transform animation** to the *secant line, making it visually change into the **tangent line Mobject* at point P"
        "Use the **MathTex class** to display the simplified slope expression that results from the limit: *$m_{\text{tan}} = \lim_{\Delta x \to 0} (2x + \Delta x) = 2x$*"
        "Use the **Create animation** to draw the **FunctionGraph** of the derivative *$f'(x) = 2x$* on the same axes, using a contrasting color (e.g., GREEN)"
        "Finally, display the core differential notation using large **MathTex*: **$\frac{d}{dx}(x^2) = 2x$*"
        ]

        eg4. user - Explain the area of a circle
        "enhanced prompt = [Use the **Circle class** to draw a filled circle and apply **set_fill** with a distinct color (e.g., TEAL), labeling the radius $r$ using the **Line and MathTex classes**"
        "Use the **MathTex class** to prominently display the circumference formula: *$C = 2\pi r$*"
        "Define the circle's area using a high number of small, equal **Sector Mobjects** (e.g., $n=16$ or $n=32$) and apply an **alternate_colors** utility to the **VGroup** of sectors for clarity"
        "Use the **Animate function** with **LaggedStart** and **Succession** to move the sectors: first by **Translate** them outwards from the center, then by **Rotate** them so they are vertical and alternating direction"
        "Apply a **Transform animation** to the **VGroup of sectors** to smoothly arrange them into a shape that approaches a **Rectangle**"
        "Use the **Line and MathTex classes** to draw the *height* measurement of the resulting rectangle and label it as the circle's radius, *$r$*"
        "Use the **Line and MathTex classes** to draw the *base* measurement of the resulting rectangle and label it as half the circumference: *$\frac{1}{2}(2\pi r) = \pi r$*"
        "Display the intermediate calculation using **MathTex**: $\text{Area} = \text{base} \times \text{height} = (\pi r) \times (r)$"
        "Display the final *area formula* for the circle using large, bold **MathTex*: **$A = \pi r^2$*, using a **GrowFromCenter** animation for emphasis"
        "Optionally, use an **Indicate or Flash animation** to show that the area of the final **Rectangle Mobject** is equal to the area of the original **Circle Mobject**"
        ]

        eg5. user - Explain Simple Harmonic Motion 
        "enhanced prompt = [Use the **Line class** to draw a fixed vertical wall on the left, and the **Spring class** to draw a horizontal spring Mobject attached to the wall"
        "Use the **Square class** to create a block Mobject (mass $m$) attached to the right end of the spring, resting on a horizontal **Line** representing a frictionless surface"
        "Draw a **DashedLine** to indicate the *equilibrium position* of the block and label it *$x=0$* using **Text or MathTex**"
        "Animate the block being manually displaced to the right to a maximum position, labeled *$x=+A$* (amplitude)"
        "Use the **Vector class** to draw the *restoring force vector* $\vec{F}$ pointing back toward $x=0$, applying the **always_redraw utility** to ensure the vector's length and direction update with the block's position"
        "Display the mathematical description of the restoring force near the block using **MathTex*: **$\vec{F}=-k\vec{x}$* (Hooke's Law)"
        "Start the **Animate function** using **MoveToTarget** or a custom function to make the block oscillate smoothly between *$x=+A$* and *$x=-A$*"
        "Simultaneously, use the **Axes class** to draw a separate graph below the main setup with axes labeled $t$ (time) and $x$ (position)"
        "Use the **FunctionGraph class** and an **Update function** to plot a *sine wave* (or cosine wave) Mobject on the graph in real-time, representing the block's position $x(t)$ vs. time $t$"
        "Highlight the points where *velocity ($\vec{v}$) is zero* (at $x=\pm A$) and where *acceleration ($\vec{a}$) is maximum*"
        "Display the formula for the *period ($T$)* of the oscillation using large **MathTex*: **$T = 2\pi\sqrt{\frac{m}{k}}$*"
        ]

        eg6. user - explain normal distribution
        "enhanced prompt = [Use the **Axes class** with x_range and y_range defined to draw a Cartesian coordinate system, labeling the x-axis as '$x$' and the y-axis as '$f(x)$' (probability density)"
        "Use the **FunctionGraph class** to plot the iconic *bell-shaped curve Mobject* of the Normal Distribution, setting its color (e.g., BLUE)"
        "Use the **DashedLine class** to draw a vertical line from the peak of the curve down to the x-axis, and use **MathTex** to label this point as the *mean, $\mu$*"
        "Use the **Line class** to mark and label the standard deviation points: *$\mu \pm \sigma$, **$\mu \pm 2\sigma$, and **$\mu \pm 3\sigma$* along the x-axis using **MathTex**"
        "Use the **Area Mobject** or **add_area_under_graph function** to shade the region under the curve between *$\mu - \sigma$* and *$\mu + \sigma$*"
        "Use **Text or MathTex** to display the percentage within this shaded region: *$68.2\%$*"
        "Display the full *Probability Density Function (PDF)* formula for the Normal Distribution using large, centered **MathTex*: **$f(x)=\frac{1}{\sigma\sqrt{2\pi}}e^{-\frac{1}{2}(\frac{x-\mu}{\sigma})^2}$*"
        "Animate a **Transform or MoveToTarget animation** where the entire bell curve smoothly *translates horizontally, while the **$\mu$ label updates dynamically* to show the effect of changing the mean"
        "Animate a second **Transform or FadeTransform animation** where the bell curve *changes its shape: becoming wider and flatter, then narrower and taller, while the **$\sigma$ label updates dynamically* to show the effect of changing the standard deviation (variance)"
        "Shade the areas for *$95.4\%$* (between $\mu \pm 2\sigma$) and *$99.7\%$* (between $\mu \pm 3\sigma$), using distinct colors or **Animate** effects to highlight these regions successively"
        "Use the **Dot class** to mark the *inflection points* on the curve and draw a **DashedLine** from them to the x-axis to show their relation to $\mu \pm \sigma$"
        ]
        LIMIT THE NUMBER OF INSTRUCTIONS TO BE ALWAYS BE IN RANGE OF 1-10
        each string generated be kind of independent without depending on previous list and without loosing the context
        do not use latex or related methods or classes, prefer doing those things without latex related methods        
    """
    structured_llm = llm.with_structured_output(output_format)
    response = structured_llm.invoke([
        {"role": "system", "content": prompt}, {"role": "user", "content": state["prompt"]}
    ])

    ai_msg = AIMessage(
        content=f"The user query has been broken down into instructions "
    )
    
    return {
        "messages": [ai_msg],
        "instructions": response.steps
    }
