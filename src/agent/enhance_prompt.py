from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from pydantic import BaseModel
from typing import List

from agent.graph_state import State
llm = init_chat_model("openai:gpt-5")

class output_format(BaseModel):
    steps: List[str]
    

def enhanced_prompt(state: State):
    prompt = """   

        You are an expert script writer of animated videos. You have to break down the user prompt into enhanced prompt. Decompose the user's request into atomic, Manim-specific actions to effectively query your specialized vector database. Each sub-query should be a standalone, retrievable command or concept. Make the enhanced prompt exceptionally descriptive and effective for a RAG system searching Manim commands.

        When a user provides a minimal or vague prompt—something short like “cat jumping” or “ball rolling”—you must assume they want a simple visual animation of that action. Fill in the missing details automatically. Include a background, a main object (like the cat or ball), a movement or behavior (jumping, rolling, bouncing, rotating), and a basic camera setup. Convert that small idea into three to eight clear animation steps. The output should look like a short storyboard made of individual, self-contained Manim commands.

        When the user gives a proper educational concept, like a topic from physics or mathematics, break it down visually using clear and logical steps. Show setup, labeling, transformations, and results, but do it without LaTeX.

        egs -
        eg1 . user - explain projectile motion
        enhanced_prompt = [
        "Use the Axes class with tick marks and labels for x and y to draw a full first-quadrant coordinate system, and set the NumberPlane as a faint background grid.",
        "Use the Dot or Sphere class to create the projectile object (a ball), starting at the origin.",
        "Draw the initial velocity using the Vector class and label it with Text('v0'); draw the launch angle using the Angle class and label it with Text('theta').",
        "Use a Transform animation to split the initial velocity vector into its two components: a horizontal component labeled Text('v0x') and a vertical component labeled Text('v0y').",
        "Display the component relationships using Text('v0x = v0 * cos(theta)') and Text('v0y = v0 * sin(theta)').",
        "Define the path of motion using the ParametricFunction class based on the projectile equations: y(t) = (v0 * sin(theta)) * t - 0.5 * g * t^2 and x(t) = (v0 * cos(theta)) * t.",
        "Use the MoveAlongPath animation to make the ball follow the defined parabolic curve.",
        "Use an always_redraw updater to show a horizontal velocity arrow labeled Text('vx') that stays constant in length during the motion.",
        "Use another always_redraw updater to show a vertical velocity arrow labeled Text('vy') that decreases to zero at the peak and increases downward during descent.",
        "Use the Arrow class to draw a constant downward acceleration arrow near the projectile labeled Text('g = 9.8 m/s^2').",
        "At the top of the trajectory, use Succession to pause the animation, zoom in, and use FadeTransform to highlight that Text('vy = 0') while Text('vx') is at its maximum."
        ]


        eg2. user - explain  the pythagoras theorem 
        enhanced_prompt = [
        "Use the Polygon class or Triangle class to draw a clearly visible right-angled triangle, ensuring the right angle is clearly marked with a Square Mobject or an arc.",
        "Use the Text class to label each vertex of the triangle as A, B, and C (with C being the right angle).",
        "Use the Line class to represent each side, and then use Text to label the lengths of the sides opposite the vertices as 'a' (vertical leg), 'b' (horizontal leg), and 'c' (hypotenuse).",
        "Construct a large, distinct Square Mobject on the outer side of leg a, explicitly using Square.set_fill with a specific color (e.g., BLUE) and Text to label its area as 'a²'.",
        "Construct a large, distinct Square Mobject on the outer side of leg b, explicitly using Square.set_fill with a different color (e.g., RED) and Text to label its area as 'b²'.",
        "Construct a large, distinct Square Mobject on the outer side of the hypotenuse c, explicitly using Square.set_fill with a third color (e.g., GREEN) and Text to label its area as 'c²'.",
        "Animate a FadeOut of the original triangle, leaving only the three squares.",
        "Perform a Transform animation or a sequence of Rotate and Translate animations on the Square Mobject labeled 'a²' and the Square Mobject labeled 'b²'.",
        "The goal of the animation is to show the pieces of 'a²' and 'b²' being cut and rearranged (e.g., using Difference or Intersection Mobjects to simulate cuts) to perfectly fill the area of the Square Mobject labeled 'c²'.",
        "Highlight the moment of perfect fit with a Flash animation or a color pulse on 'c²'.",
        "Display the final Pythagorean theorem equation prominently in the center of the screen using large, bold Text: 'a² + b² = c²'."
        ]


        eg3. user - Show the derivative of x^2
        enhanced_prompt = [
        "Use the Axes class with labeled x and y axes (for example, label them as 'x' and 'f(x)') to draw a standard Cartesian plane, optionally using a NumberPlane grid for context.",
        "Plot the function f(x) = x² using the FunctionGraph class, setting a distinct color such as YELLOW.",
        "Use the Dot class to place a point Mobject labeled 'P' at a general point on the curve, representing coordinates (x, x²).",
        "Use another Dot class to place a second point Mobject labeled 'Q' at a nearby location on the curve, representing coordinates (x + delta_x, (x + delta_x)²).",
        "Use the DashedLine class to draw the horizontal distance labeled 'delta_x' and the vertical distance labeled 'delta_f' between points P and Q.",
        "Draw a Line Mobject representing the secant line passing through points P and Q.",
        "Use the Text class to display the formula for the slope of the secant line: 'm_sec = (delta_y / delta_x) = ((x + delta_x)² - x²) / delta_x'.",
        "Animate point Q using the MoveAlongPath method to smoothly approach and nearly coincide with point P, showing the limit process where delta_x approaches 0.",
        "Apply a Transform animation to the secant line, making it visually change into the tangent line at point P.",
        "Use the Text class to display the simplified slope expression that results from the limit: 'm_tan = limit as delta_x → 0 of (2x + delta_x) = 2x'.",
        "Use the Create animation to draw the FunctionGraph of the derivative f'(x) = 2x on the same axes using a contrasting color such as GREEN.",
        "Finally, display the core differential notation using large Text: 'd/dx (x²) = 2x'."
        ]


        eg4. user - Explain the area of a circle
        enhanced_prompt = [
        "Use the Circle class to draw a filled circle and apply set_fill with a distinct color (for example, TEAL). Label the radius as 'r' using the Line and Text classes.",
        "Use the Text class to prominently display the circumference formula: 'C = 2 * pi * r'.",
        "Define the circle's area using many small, equal Sector Mobjects (for example, n = 16 or n = 32) and apply an alternate_colors utility to the VGroup of sectors for visual clarity.",
        "Use the Animate function with LaggedStart and Succession to move the sectors: first Translate them outward from the center, then Rotate them so they stand vertically and alternate in direction.",
        "Apply a Transform animation to the VGroup of sectors to smoothly arrange them into a shape that looks like a Rectangle.",
        "Use the Line and Text classes to draw the height measurement of the resulting rectangle and label it as the circle's radius 'r'.",
        "Use the Line and Text classes to draw the base measurement of the rectangle and label it as half the circumference: '0.5 * (2 * pi * r) = pi * r'.",
        "Display the intermediate calculation using Text: 'Area = base * height = (pi * r) * (r)'.",
        "Display the final area formula for the circle using large, bold Text: 'A = pi * r²', and use a GrowFromCenter animation for emphasis.",
        "Optionally, use an Indicate or Flash animation to show that the area of the final Rectangle Mobject equals the area of the original Circle Mobject."
        ]


        eg5. user - Explain Simple Harmonic Motion 
        enhanced_prompt = [
        "Use the Line class to draw a fixed vertical wall on the left, and the Spring class to draw a horizontal spring Mobject attached to the wall.",
        "Use the Square class to create a block Mobject (mass 'm') attached to the right end of the spring, resting on a horizontal Line representing a frictionless surface.",
        "Draw a DashedLine to indicate the equilibrium position of the block and label it as 'x = 0' using the Text class.",
        "Animate the block being manually displaced to the right to a maximum position labeled 'x = +A' to represent the amplitude.",
        "Use the Vector class to draw a restoring force arrow labeled 'F' pointing back toward x = 0, applying the always_redraw utility so that its direction and length update with the block's position.",
        "Display the mathematical description of the restoring force near the block using Text: 'F = -k * x' (Hooke's Law).",
        "Use the Animate function with MoveToTarget or a custom motion function to make the block oscillate smoothly between 'x = +A' and 'x = -A'.",
        "At the same time, use the Axes class to draw a separate graph below the setup with axes labeled 't' for time and 'x' for position.",
        "Use the FunctionGraph class with an Update function to plot a sine or cosine wave in real time, showing how x changes with t.",
        "Highlight the points where velocity (v) is zero, which occur at x = +A and x = -A, and where acceleration (a) is maximum.",
        "Display the formula for the oscillation period using large Text: 'T = 2 * pi * sqrt(m / k)'."
        ]


        eg6. user - explain normal distribution
        enhanced_prompt = [
        "Use the Axes class with defined x_range and y_range to draw a Cartesian coordinate system, labeling the x-axis as 'x' and the y-axis as 'f(x)' to represent probability density.",
        "Use the FunctionGraph class to plot the well-known bell-shaped curve of the Normal Distribution, setting its color to BLUE.",
        "Use the DashedLine class to draw a vertical line from the peak of the curve down to the x-axis, and label this point with Text('mean, mu').",
        "Use the Line class to mark and label the standard deviation points along the x-axis using Text: 'mu ± sigma', 'mu ± 2sigma', and 'mu ± 3sigma'.",
        "Use the Area Mobject or add_area_under_graph function to shade the region under the curve between 'mu - sigma' and 'mu + sigma'.",
        "Use the Text class to display the percentage within this shaded region: '68.2%'.",
        "Display the Probability Density Function formula for the Normal Distribution using large centered Text: 'f(x) = (1 / (sigma * sqrt(2 * pi))) * e^(-0.5 * ((x - mu) / sigma)^2)'.",
        "Animate a Transform or MoveToTarget animation where the entire bell curve smoothly shifts horizontally, while the 'mu' label updates dynamically to show the effect of changing the mean.",
        "Animate a second Transform or FadeTransform animation where the bell curve changes its shape — becoming wider and flatter, then narrower and taller — while the 'sigma' label updates dynamically to show the effect of changing standard deviation.",
        "Shade the areas for '95.4%' (between mu ± 2sigma) and '99.7%' (between mu ± 3sigma), using distinct colors or Animate effects to highlight these regions one after another.",
        "Use the Dot class to mark the inflection points on the curve and draw a DashedLine from them to the x-axis to show their relation to 'mu ± sigma'."
        ]

        LIMIT THE NUMBER OF INSTRUCTIONS TO BE ALWAYS BE IN RANGE OF 1-10
        Each string generated be independent without depending on previous list and without loosing the context.
        Follow these same principles for all topics. Always break things into clear, independent steps, never use LaTeX, automatically add missing context for short prompts, and keep your instructions short, useful, and technically sound.       
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
