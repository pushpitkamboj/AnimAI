_prompt_scene_plan = """You are an expert in educational video production, instructional design. Please design a high-quality video to provide in-depth explanation on the required user prompt.

raw user prompt - {prompt}

**Scene Breakdown:**

Plan individual scenes. For each scene please provide the following:

*   **Scene Title:** Short, descriptive title (2-5 words).
*   **Scene Purpose:** Learning objective of this scene. How does it connect to previous scenes?
*   **Scene Description:** Detailed description of scene content.


Requirements:
1. Scenes must build progressively, starting from foundational concepts and advancing to more complex ideas to ensure a logical flow of understanding for the viewer. Each scene should naturally follow from the previous one, creating a cohesive learning narrative. Start with simpler scene layouts and progressively increase complexity in later scenes.
2. The total number of scenes should be between 1-4. If the concept is straightforward and very simple keep it to 1 scene only (eg. draw a circle/square etc). only exceed the scenes when the concept is really difficult and can be difficult to explain in 1 scene, else for most of prompts 1 scene is enough
3. Learning objectives should be distributed evenly across the scenes.
4. The total video duration must be under 30-180 seconds.
5. It is essential to use the exact output format, tags, and headers as specified in the prompt.
6. Maintain consistent formatting throughout the entire scene plan.
7. **No External Assets:** Do not import any external files (images, audio, video). *Use only Manim built-in elements and procedural generation.
8. **Focus on in-depth explanation of the theorem. Do not include any promotional elements (like YouTube channel promotion, subscribe messages, or external resources) or quiz sessions. Detailed example questions are acceptable and encouraged.**

Note: High-level plan. Detailed scene specifications will be generated later, ensuring adherence to safe area margins and minimum spacing. The spatial constraints defined above will be strictly enforced in subsequent planning stages.

at last also give an overall name to the scene as IndividualScene, make sure to write the scene name with this format => binary_search_explained, deadlock_management, architecture_advantages... 
"""

